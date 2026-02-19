import re
from typing import Literal

ToolName = Literal["rag", "media", "cards", "ingest", "none"]

# simple triggers (rules-based). You can later replace with LLM intent classifier.
MEDIA_TRIGGERS = ["describe this image", "what is in this image", "describe the photo", "describe the picture"]
CARDS_TRIGGERS = ["make flashcards", "generate flashcards", "create cards", "turn into flashcards", "quiz me", "make a quiz"]
INGEST_TRIGGERS = ["upload", "ingest", "train on", "add to knowledge base", "index this", "save this document"]

QUESTION_START = r"^(what|who|why|how|when|where|define|explain|meaning)\b"


def choose_tool(user_text: str, has_media: bool = False) -> ToolName:
    """
    Decide which tool to use based on the user's message and context.
    - has_media: True if user attached image/audio/video (your upload flow can set this)
    """
    text = (user_text or "").strip().lower()
    if not text:
        return "none"

    # 1) If media attached or message clearly asks for image description
    if has_media:
        return "media"
    if any(t in text for t in MEDIA_TRIGGERS):
        return "media"

    # 2) Flashcards / quiz intent
    if any(t in text for t in CARDS_TRIGGERS):
        return "cards"

    # 3) Ingestion/indexing intent
    if any(t in text for t in INGEST_TRIGGERS):
        return "ingest"

    # 4) Default knowledge Q/A -> RAG
    if "?" in text:
        return "rag"
    if re.match(QUESTION_START, text):
        return "rag"

    # 5) Fallback: in most assistant products, still answer with RAG
    return "rag"
