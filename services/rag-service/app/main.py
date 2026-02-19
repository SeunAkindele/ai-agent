from fastapi import FastAPI
from app.api.v1.routes_rag import router as rag_router

app = FastAPI(
    title="RAG Service",
    description="RAG service with HTTP API + MCP tool",
    version="0.1.0",
)

app.include_router(rag_router, prefix="/rag")

@app.get("/")
def root():
    return {"service": "rag-service", "status": "running"}
