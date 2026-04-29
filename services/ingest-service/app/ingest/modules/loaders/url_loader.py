# url_loader.py

import requests
from typing import Union
from app.infrastructure.ingest_parsers.data_parser import DataParser

class URLLoader:
    def __init__(self):
        self.data_parser = DataParser()

    def load_url(self, url: str, data_type: str) -> Union[str, bytes]:
        """Fetch data from a URL based on the data type."""
        
        # Fetch data from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for invalid responses
        
        if data_type == 'text':  # Process text data
            return self._process_text(response.text)
        elif data_type == 'image':  # Process image URLs
            return self._process_image(response.content)
        elif data_type == 'audio':  # Process audio data (you may send it to C++ sidecar here)
            return self._process_audio(response.content)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    def _process_text(self, text: str) -> str:
        """Preprocess text data (clean and tokenize)."""
        return self.data_parser.preprocess_text(text)  # Using data_parser to clean and process the text

    def _process_image(self, content: bytes) -> bytes:
        """Handle image data (download and optionally process)."""
        # Here, we just return the content, but you can add image processing if needed
        return content

    def _process_audio(self, content: bytes) -> bytes:
        """Process audio content (e.g., send to C++ sidecar for processing)."""
        # Send to C++ sidecar for audio processing (if required)
        # You can call your C++ sidecar like this:
        # result = subprocess.run(["./cpp-sidecar/audio_loader", content], capture_output=True)
        # return result.stdout
        return content