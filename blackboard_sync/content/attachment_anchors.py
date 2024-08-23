import requests
from urllib.parse import urlparse, unquote
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


def download_from_url(url: str):
    """Download a file from a direct URL."""
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Ensure the request was successful
    return response.raw


class URLAttachment:
    """File downloaded directly from a URL."""

    def __init__(self, url: str, filename: str = None):
        if url:
            # Direct download from a URL
            self.filename = filename or self.extract_filename_from_url(url)
            self.stream = download_from_url(url)
        else:
            raise ValueError("A valid URL must be provided for direct download.")

    @staticmethod
    def extract_filename_from_url(url: str) -> str:
        """Extracts a filename from the URL."""
        # Try to extract a filename from the URL
        parsed_url = urlparse(url)
        path = parsed_url.path  # Get the path from the URL

        # Decode any percent-encoded characters in the URL
        decoded_path = unquote(path)

        # Check if the path ends with .pdf (case-insensitive)
        if decoded_path.lower().endswith(".pdf"):
            filename = Path(decoded_path).name
            return filename
        return "downloaded_file.pdf"

    def write(self, path: Path, executor: ThreadPoolExecutor):
        """Write the file to the specified path."""
        # Save the file to the specified path
        with open(path / self.filename, 'wb') as f:
            for chunk in self.stream:
                f.write(chunk)