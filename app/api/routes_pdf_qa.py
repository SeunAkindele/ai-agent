# app/routes_pdf_qa.py

import io
import json
import os
from typing import Dict, List
from uuid import uuid4

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# Very simple in-memory PDF store: {doc_id: [page_text1, page_text2, ...]}
PDF_STORE: Dict[str, List[str]] = {}


class PdfUploadResponse(BaseModel):
    doc_id: str
    pages: int


class PdfQuestionRequest(BaseModel):
    doc_id: str
    question: str


class PdfQuestionResponse(BaseModel):
    answer: str
    used_pages: List[int] = []          # 1-based page numbers
    context_snippet: str | None = None  # short text the model relied on


PDF_QA_SCHEMA = PdfQuestionResponse.model_json_schema()

PDF_QA_SYSTEM_PROMPT = (
    "You are a PDF question answering assistant.\n"
    "You will receive the text content of a PDF document with page markers.\n"
    "Answer ONLY using information from that content.\n\n"
    "Return ONLY valid JSON that matches this schema:\n"
    "- answer (string): concise answer to the question.\n"
    "- used_pages (array of integers): page numbers (1-based) you relied on.\n"
    "- context_snippet (string): short excerpt supporting your answer.\n"
    "If the answer is not in the document, set answer to a clear 'I don't know' type message.\n"
)


@router.post("/pdf/upload", response_model=PdfUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
        raise HTTPException(
            status_code=500,
            detail="Ollama configuration is missing. Set OLLAMA_BASE_URL and OLLAMA_MODEL.",
        )

    try:
        raw = await file.read()
        reader = PdfReader(io.BytesIO(raw))

        pages_text: List[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages_text.append(text.strip())

        if not any(pages_text):
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from this PDF.",
            )

        doc_id = str(uuid4())
        PDF_STORE[doc_id] = pages_text

        return PdfUploadResponse(doc_id=doc_id, pages=len(pages_text))

    except HTTPException:
        # re-raise FastAPI HTTPExceptions as is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")


@router.post("/pdf/qa", response_model=PdfQuestionResponse)
async def ask_pdf_question(payload: PdfQuestionRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty.")

    if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
        raise HTTPException(
            status_code=500,
            detail="Ollama configuration is missing. Set OLLAMA_BASE_URL and OLLAMA_MODEL.",
        )

    pages = PDF_STORE.get(payload.doc_id)
    if not pages:
        raise HTTPException(status_code=404, detail="PDF not found or expired.")

    # Simple Stage-1 approach: send all pages with page markers.
    # (Stage 2 will replace this with a vector DB + retrieval.)
    marked_text_parts: List[str] = []
    for i, txt in enumerate(pages, start=1):
        marked_text_parts.append(f"[PAGE {i}]\n{txt}")

    full_marked_text = "\n\n".join(marked_text_parts)

    ollama_body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": PDF_QA_SCHEMA,
        "messages": [
            {"role": "system", "content": PDF_QA_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "PDF content:\n"
                    f"{full_marked_text}\n\n"
                    f"Question: {payload.question}"
                ),
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=180) as http:
            resp = await http.post(f"{OLLAMA_BASE_URL}/api/chat", json=ollama_body)
            resp.raise_for_status()
            data_raw = resp.json()

        content = (data_raw.get("message") or {}).get("content") or "{}"
        content = content.strip()
        data = json.loads(content)

        return PdfQuestionResponse(
            answer=str(data.get("answer", "")),
            used_pages=[int(p) for p in data.get("used_pages", []) or []],
            context_snippet=(
                str(data["context_snippet"])
                if data.get("context_snippet") is not None
                else None
            ),
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e.response.text}")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Model did not return valid JSON for PDF QA.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF QA failed: {e}")
