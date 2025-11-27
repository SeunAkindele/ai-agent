from fastapi import FastAPI
from app.api.routes_text import router as text_router

app = FastAPI(title="AI Agent")

app.include_router(text_router, prefix="/ai-agent/v1", tags=["ai_agent"])

@app.get("/")
def read_root():
    return {"message": "AI agent backend is running..."}

@app.get("/health")
def health():
    return {"message": "API is working"}
