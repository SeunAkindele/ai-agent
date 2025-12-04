from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.api.routes_text import router as text_router
from app.api.routes_rewrite import router as rewrite_router

app = FastAPI(title="AI Agent")

app.include_router(text_router, prefix="/ai-agent/v1", tags=["ai_agent"])
app.include_router(rewrite_router, prefix="/ai-agent/v1", tags=["ai_agent"])

@app.get("/")
def read_root():
    return {"message": "AI agent backend is running..."}

@app.get("/health")
def health():
    return {"message": "API is working"}
