import json, os

from dotenv import load_dotenv
load_dotenv()

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
    text: str = Field(..., description="The text you want to summarize.")
    style: SummaryStyle = Field(
        default=SummaryStyle.short,
        description="Summary style: 'short' or 'detailed'.",
        examples=["short"],
    )


class TextSummarizeResponse(BaseModel):
    summary: str = Field(..., description="The generated summary of the text.")
    key_points: List[str] = Field(default_factory=list)


@router.post(
    "/summarize",
    summary="Summarize Text",
    response_model=TextSummarizeResponse,
)

async def summarize_text(payload: TextSummarizeRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty.")

    schema = TextSummarizeResponse.model_json_schema()

    system_prompt = (
        "Return ONLY valid JSON that matches the provided JSON schema.\n"
        "Keys: summary (string), key_points (array of strings).\n"
        "If style='short': summary max 3 sentences, key_points max 3.\n"
        "If style='detailed': summary up to ~8 sentences, key_points up to 8.\n"
    )

    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": schema,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"style: {payload.style.value}\n\ntext:\n{payload.text}",
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120) as http:
            r = await http.post(f"{OLLAMA_BASE_URL}/api/chat", json=body)
            r.raise_for_status()
            resp = r.json()

        content = (resp.get("message") or {}).get("content") or "{}"
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
