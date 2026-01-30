from fastapi import APIRouter
from app.rag.pipeline import RAGPipeline
from app.schemas.rag_request import AskRequest
from app.schemas.rag_response import AskResponse

router = APIRouter()

pipeline = RAGPipeline()

@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a question using RAG",
    description="Submit a question and receive an answer generated via the RAG pipeline."
)
def ask_question(payload: AskRequest):
    answer = pipeline.run(payload.question)

    return AskResponse(
        question=payload.question,
        answer=answer
    )
