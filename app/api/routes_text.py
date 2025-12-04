import json
import os
from enum import Enum
from typing import List

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

class SummaryStyle(str, Enum):
    short = "short"
    detailed = "detailed"

class TextSummarizeRequest(BaseModel):
    text: str
    style: SummaryStyle = SummaryStyle.short

class TextSummarizeResponse(BaseModel):
    summary: str
    key_points: List[str] = Field(default_factory=list)

# Build JSON schema once for the model
TEXT_SUMMARY_SCHEMA = TextSummarizeResponse.model_json_schema()

SYSTEM_PROMPT = (
    "Return ONLY valid JSON that matches the provided JSON schema.\n"
    "Keys: summary (string), key_points (array of strings).\n"
    "If style='short': summary max 3 sentences, key_points max 3.\n"
    "If style='detailed': summary up to ~8 sentences, key_points up to 8.\n"
)

@router.post("/summarize", response_model=TextSummarizeResponse)
async def summarize_text(payload: TextSummarizeRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty.")

    if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
        raise HTTPException(
            status_code=500,
            detail="Ollama configuration is missing. Set OLLAMA_BASE_URL and OLLAMA_MODEL.",
        )

    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": TEXT_SUMMARY_SCHEMA,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"style: {payload.style.value}\n\ntext:\n{payload.text}",
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120) as http:
            resp = await http.post(f"{OLLAMA_BASE_URL}/api/chat", json=body)
            resp.raise_for_status()
            data_raw = resp.json()

        content = (data_raw.get("message") or {}).get("content") or "{}"
        content = content.strip()
        data = json.loads(content)

        return TextSummarizeResponse(
            summary=str(data.get("summary", "")),
            key_points=list(data.get("key_points", []) or []),
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e.response.text}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Model did not return valid JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")
