from app.core.tool_decision import ToolDecision


def choose_tool(message: str, has_media: bool = False) -> ToolDecision:
    text = (message or "").strip().lower()

    if not text:
        return ToolDecision(
            tool_name="none",
            confidence=0.10,
            reason="empty_message",
        )

    if has_media:
        return ToolDecision(
            tool_name="media",
            confidence=0.95,
            reason="request_contains_media",
        )

    ingest_keywords = [
        "upload", "ingest", "index document", "index file", "re-index"
    ]
    if any(word in text for word in ingest_keywords):
        return ToolDecision(
            tool_name="ingest",
            confidence=0.90,
            reason="document_ingestion_intent",
        )

    cards_keywords = [
        "flashcard", "flash card", "quiz card", "study card", "cards"
    ]
    if any(word in text for word in cards_keywords):
        return ToolDecision(
            tool_name="cards",
            confidence=0.82,
            reason="cards_generation_intent",
        )

    rag_keywords = [
        "what is", "who is", "explain", "tell me about", "how does",
        "why is", "summarize", "search", "find information", "answer this",
        "question about", "knowledge base", "document", "docs"
    ]
    if any(word in text for word in rag_keywords):
        return ToolDecision(
            tool_name="rag",
            confidence=0.80,
            reason="knowledge_retrieval_intent",
        )

    return ToolDecision(
        tool_name="none",
        confidence=0.20,
        reason="no_matching_tool",
    )