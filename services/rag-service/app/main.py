from fastapi import FastAPI
from app.api.v1.routes_rag import router as rag_router

app = FastAPI(
    title="RAG Service",
    description="Modular RAG service with measure & refine",
    version="0.1.0",
)

# Register routes
app.include_router(rag_router, prefix="/rag")

@app.get("/")
def root():
    return {
        "service": "rag-service",
        "status": "running"
    }
