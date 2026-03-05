# csv_loader.py

import subprocess
from app.infrastructure.ingest_parsers.data_parser import DataParser
from typing import List

class CsvLoader:
    def __init__(self):
        self.data_parser = DataParser()

    def load_csv(self, source: str) -> List[str]:
        """Use C++ sidecar to process CSV or preprocess CSV data."""
        result = subprocess.run(
            ["./cpp-sidecar/csv_loader", source], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"CSV processing failed: {result.stderr}")
        
        # If CSV processing is done in C++, preprocess each row of data
        raw_data = result.stdout.splitlines()
        return [self.data_parser.preprocess_text(row) for row in raw_data]