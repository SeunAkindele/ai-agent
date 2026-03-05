# text_loader.py

from app.infrastructure.ingest_parsers.data_parser import DataParser
from typing import List

class TextLoader:
    def __init__(self):
        self.data_parser = DataParser()

    def load_text(self, source: str) -> List[str]:
        """Load and preprocess text data from a file."""
        with open(source, 'r') as file:
            raw_data = file.readlines()

        # Preprocess each line of text using data_parser
        return [self.data_parser.preprocess_text(line) for line in raw_data]