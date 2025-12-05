import json
import os
from enum import Enum
from typing import List

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


class SummaryStyle(str, Enum):
    short = "short"
    detailed = "detailed"


class UrlSummarizeRequest(BaseModel):
    url: HttpUrl
    style: SummaryStyle = SummaryStyle.short


class UrlSummarizeResponse(BaseModel):
    summary: str
    key_points: List[str] = []


URL_SUMMARY_SCHEMA = UrlSummarizeResponse.model_json_schema()

SYSTEM_PROMPT = (
    "You are a URL article summarization assistant.\n"
    "You will be given the cleaned text content of a web page.\n\n"
    "Return ONLY valid JSON that matches the provided JSON schema.\n"
    "Fields:\n"
    "- summary (string): a concise summary of the article.\n"
    "- key_points (array of strings): bullet key points.\n\n"
    "If style='short': summary max 3 sentences, key_points max 3.\n"
    "If style='detailed': summary up to ~8 sentences, key_points up to 8.\n"
    "Do not add extra keys. Do not include metadata like ads or navigation."
)


async def _fetch_and_extract_text(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch URL: {e}",
        )

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    body = soup.body or soup
    text = body.get_text(separator="\n", strip=True)

    if not text or len(text) < 200:
        raise HTTPException(
            status_code=400,
            detail="The page does not contain enough readable text to summarize.",
        )

    return text[:8000]


@router.post("/url/summarize", response_model=UrlSummarizeResponse)
async def summarize_url(payload: UrlSummarizeRequest):
    if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
        raise HTTPException(
            status_code=500,
            detail="Ollama configuration is missing. Set OLLAMA_BASE_URL and OLLAMA_MODEL.",
        )

    page_text = await _fetch_and_extract_text(str(payload.url))

    ollama_body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": URL_SUMMARY_SCHEMA,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"style: {payload.style.value}\n\n"
                    f"Article text:\n{page_text}"
                ),
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=ollama_body)
            resp.raise_for_status()
            raw = resp.json()

            content = (raw.get("message") or {}).get("content") or "{}"
            content = content.strip()
            data = json.loads(content)

            return UrlSummarizeResponse(
                summary=str(data.get("summary", "")),
                key_points=list(data.get("key_points", []) or []),
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e.response.text}")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Model did not return valid JSON for URL summarization.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URL summarization failed: {e}")
