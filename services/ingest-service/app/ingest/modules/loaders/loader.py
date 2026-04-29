# loader.py

from app.ingest.modules.loaders.url_loader import URLLoader
from app.ingest.modules.loaders.text_loader import TextLoader
from app.ingest.modules.loaders.csv_loader import CsvLoader
from app.ingest.modules.loaders.audio_loader import AudioLoader

class Loader:
    def __init__(self):
        self.url_loader = URLLoader()  # URL Loader
        self.text_loader = TextLoader()  # Text Loader
        self.csv_loader = CsvLoader()  # CSV Loader
        self.audio_loader = AudioLoader()  # Audio Loader

    def load_data(self, source: str, data_type: str):
        """Select loader based on the data type (url, audio, csv, text)."""
        if data_type == 'url':
            return self.url_loader.load_url(source, data_type)  # Use URL loader for URL data
        elif data_type == 'audio':
            return self.audio_loader.load_audio(source)  # Use Audio loader (C++ sidecar for processing)
        elif data_type == 'csv':
            return self.csv_loader.load_csv(source)  # Use CSV loader (C++ sidecar for processing)
        elif data_type == 'text':
            return self.text_loader.load_text(source)  # Use Text loader (with preprocessing)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")