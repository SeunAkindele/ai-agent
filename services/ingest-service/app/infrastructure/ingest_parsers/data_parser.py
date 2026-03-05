# data_parser.py

import re

class DataParser:
    def preprocess_text(self, text: str) -> str:
        """Basic text preprocessing: remove unwanted characters, lowercasing, etc."""
        # Remove unwanted characters (e.g., punctuation)
        text = re.sub(r'[^\w\s]', '', text)
        # Lowercase the text
        text = text.lower()
        return text

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        return text.split()  # Simple split, can be improved with NLTK/spacy