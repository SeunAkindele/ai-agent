import io
import json
import os
from typing import List

import httpx
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


class CsvInsightsResponse(BaseModel):
    summary: str
    key_points: List[str] = []
    column_stats: dict = {}  # optional stats returned by AI


CSV_INSIGHTS_SCHEMA = CsvInsightsResponse.model_json_schema()

SYSTEM_PROMPT = (
    "You are a CSV data insights assistant.\n"
    "You will be given the CSV contents converted to JSON rows.\n\n"
    "Return ONLY valid JSON that matches the provided JSON schema:\n"
    "- summary: a short explanation of what the dataset is about.\n"
    "- key_points: important observations about patterns, trends or anomalies.\n"
    "- column_stats: optional dictionary with stats (counts, uniqueness, notes).\n\n"
    "Rules:\n"
    "- Do NOT hallucinate values that do not appear in the dataset.\n"
    "- If some columns look numeric, you may mention trends.\n"
    "- Keep the response factual, based ONLY on the provided CSV data."
)


@router.post("/csv/insights", response_model=CsvInsightsResponse)
async def analyze_csv(file: UploadFile = File(...)):
    if file.content_type not in (
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
        raise HTTPException(
            status_code=500,
            detail="Ollama configuration is missing. Set OLLAMA_BASE_URL and OLLAMA_MODEL.",
        )

    # Step 1: Read CSV
    try:
        raw = await file.read()
        df = pd.read_csv(io.BytesIO(raw))

        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty.")

        # Convert to records (list of dicts)
        json_records = df.to_dict(orient="records")

        # Optional: limit rows to avoid context overflow
        if len(json_records) > 100:
            json_records = json_records[:100]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")

    # Step 2: Send to LLM
    ollama_body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": CSV_INSIGHTS_SCHEMA,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here is the CSV content as JSON rows:\n"
                    f"{json.dumps(json_records, indent=2)}"
                ),
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=ollama_body)
            resp.raise_for_status()
            raw_data = resp.json()

        content = (raw_data.get("message") or {}).get("content") or "{}"
        data = json.loads(content.strip())

        return CsvInsightsResponse(
            summary=str(data.get("summary", "")),
            key_points=list(data.get("key_points", []) or []),
            column_stats=dict(data.get("column_stats", {}) or {}),
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e.response.text}")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Model did not return valid JSON for CSV insights.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"CSV insights generation failed: {e}"
        )
