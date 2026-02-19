from fastapi import APIRouter
from app.schemas.rag_request import AskRequest
from app.schemas.rag_response import AskResponse
from app.rag.container import run_rag

router = APIRouter()

@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a question using RAG",
    description="Submit a question and receive an answer generated via the RAG pipeline."
)
def ask_question(payload: AskRequest):
    return run_rag(payload.question)
