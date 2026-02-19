import os

# --- RAG service HTTP base URL
# local dev: http://localhost:8001
# docker compose: http://rag-service:8001
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "http://localhost:8001")

# http client timeout
HTTP_TIMEOUT_S = float(os.getenv("HTTP_TIMEOUT_S", "20"))

# optional: allow forcing a tool (debug)
FORCE_TOOL = os.getenv("FORCE_TOOL", "").strip().lower()  # e.g. "rag"
