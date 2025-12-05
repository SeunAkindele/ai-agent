from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from app.api.routes_summarize import router as summarize_router
from app.api.routes_rewrite import router as rewrite_router
from app.api.routes_pdf_qa import router as pdf_qa_router
from app.api.routes_url_summarizer import router as url_summarizer
from app.api.routes_csv_insights import router as csv_insights

app = FastAPI(title="AI Agent")

app.include_router(summarize_router, prefix="/ai-agent/v1", tags=["ai_agent"])
app.include_router(rewrite_router, prefix="/ai-agent/v1", tags=["ai_agent"])
app.include_router(pdf_qa_router, prefix="/ai-agent/v1", tags=["ai_agent"])
app.include_router(url_summarizer, prefix="/ai-agent/v1", tags=["ai_agent"])
app.include_router(csv_insights, prefix="/ai-agent/v1", tags=["ai_agent"])

@app.get("/")
def read_root():
    return {"message": "AI agent backend is running..."}

@app.get("/health")
def health():
    return {"message": "API is working"}
