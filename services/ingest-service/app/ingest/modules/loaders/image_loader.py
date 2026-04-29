# media_loader.py

import subprocess

class ImageLoader:
    def __init__(self):
        pass


    def load_image(self, source: str) -> bytes:
        """Use C++ sidecar to process images (or use Python to download)."""
        # Example of calling C++ sidecar to process image
        result = subprocess.run(
            ["./cpp-sidecar/image_loader", source], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"Image processing failed: {result.stderr}")
        return result.stdout  # Return processed image data