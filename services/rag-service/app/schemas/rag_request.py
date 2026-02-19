from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        example="What is Retrieval-Augmented Generation?"
    )
