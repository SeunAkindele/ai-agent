import json
import os
from enum import Enum
from typing import List

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


class RewriteTone(str, Enum):
    professional = "professional"
    simple = "simple"
    casual = "casual"
    persuasive = "persuasive"


class TextRewriteRequest(BaseModel):
    text: str
    tone: RewriteTone = RewriteTone.professional


class TextRewriteResponse(BaseModel):
    rewritten_text: str
    # Optional: short explanation of what changed (you can remove if you don’t want it)
    notes: List[str] = []


TEXT_REWRITE_SCHEMA = TextRewriteResponse.model_json_schema()

SYSTEM_PROMPT = (
    "You are a text rewriting assistant.\n"
    "Return ONLY valid JSON that matches the provided JSON schema.\n"
    "Fields:\n"
    "- rewritten_text (string): the full rewritten text.\n"
    "- notes (array of strings): optional short bullet notes about changes (tone, clarity, etc.).\n"
    "Do not include the original text. Do not add extra keys.\n"
    "Rewrite the text according to the requested tone:\n"
    "- professional: formal, clear, business-like.\n"
    "- simple: easy to understand, short sentences.\n"
    "- casual: friendly, conversational.\n"
    "- persuasive: convincing, focused on benefits and impact.\n"
)


@router.post("/rewrite", response_model=TextRewriteResponse)
async def rewrite_text(payload: TextRewriteRequest):
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
        "format": TEXT_REWRITE_SCHEMA,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"tone: {payload.tone.value}\n\n"
                    f"text to rewrite:\n{payload.text}"
                ),
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

        return TextRewriteResponse(
            rewritten_text=str(data.get("rewritten_text", "")),
            notes=list(data.get("notes", []) or []),
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e.response.text}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Model did not return valid JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewriting failed: {e}")
