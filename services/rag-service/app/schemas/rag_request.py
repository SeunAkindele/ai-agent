from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        example="What is Retrieval-Augmented Generation?"
    )
