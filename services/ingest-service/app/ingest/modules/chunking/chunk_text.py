# chunking.py
from typing import List

class Chunker:
    def chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """Split text into chunks of the specified size."""
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]