# app/rag/container.py

from app.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()

def run_rag(question: str) -> dict:
    result = pipeline.run(question)
    return {
        "answer": result.answer,
        "sources": result.sources,
        "latency_ms": result.latency_ms,
    }
