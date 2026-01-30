from pydantic import BaseModel


class AskResponse(BaseModel):
    question: str
    answer: str
