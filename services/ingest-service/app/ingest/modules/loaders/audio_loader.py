# media_loader.py

import subprocess

class MediaLoader:
    def __init__(self):
        pass

    def load_audio(self, source: str) -> bytes:
        """Use C++ sidecar to process audio."""
        # Example call to C++ sidecar to process audio
        result = subprocess.run(
            ["./cpp-sidecar/audio_loader", source], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"Audio processing failed: {result.stderr}")
        return result.stdout  # Return processed audio data
