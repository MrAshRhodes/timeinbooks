"""Project Gutenberg quote source."""
import os
from typing import Generator, List, Optional

import requests

import sys
sys.path.insert(0, '..')
from config import GUTENBERG_CACHE_DIR, POPULAR_BOOK_IDS
from .base import BaseSource, SourceDocument


class GutenbergSource(BaseSource):
    """Scrape quotes from Project Gutenberg books."""

    GUTENBERG_MIRROR = "https://www.gutenberg.org"

    def __init__(self, book_ids: Optional[List[int]] = None, max_books: int = 50):
        self.book_ids = book_ids or POPULAR_BOOK_IDS
        self.max_books = max_books
        os.makedirs(GUTENBERG_CACHE_DIR, exist_ok=True)

    @property
    def name(self) -> str:
        return "Gutenberg"

    def _get_book_text(self, book_id: int) -> Optional[str]:
        """Download or retrieve cached book text."""
        cache_path = os.path.join(GUTENBERG_CACHE_DIR, f"{book_id}.txt")

        # Check cache
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        # Download
        urls = [
            f"{self.GUTENBERG_MIRROR}/cache/epub/{book_id}/pg{book_id}.txt",
            f"{self.GUTENBERG_MIRROR}/files/{book_id}/{book_id}-0.txt",
            f"{self.GUTENBERG_MIRROR}/files/{book_id}/{book_id}.txt",
        ]

        for url in urls:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    text = response.text
                    # Cache it
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    return text
            except requests.RequestException:
                continue

        print(f"  Warning: Could not download book {book_id}")
        return None

    def _get_book_metadata(self, book_id: int) -> dict:
        """Get book metadata from Gutenberg API."""
        # Simple fallback metadata
        metadata = {
            1342: {"title": "Pride and Prejudice", "author": "Jane Austen"},
            84: {"title": "Frankenstein", "author": "Mary Shelley"},
            1661: {"title": "The Adventures of Sherlock Holmes", "author": "Arthur Conan Doyle"},
            11: {"title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll"},
            98: {"title": "A Tale of Two Cities", "author": "Charles Dickens"},
            2701: {"title": "Moby Dick", "author": "Herman Melville"},
            1952: {"title": "The Yellow Wallpaper", "author": "Charlotte Perkins Gilman"},
            174: {"title": "The Picture of Dorian Gray", "author": "Oscar Wilde"},
            345: {"title": "Dracula", "author": "Bram Stoker"},
            16328: {"title": "Beowulf", "author": "Anonymous"},
            100: {"title": "The Complete Works of Shakespeare", "author": "William Shakespeare"},
            1232: {"title": "The Prince", "author": "Niccolò Machiavelli"},
            76: {"title": "Adventures of Tom Sawyer", "author": "Mark Twain"},
            74: {"title": "Adventures of Huckleberry Finn", "author": "Mark Twain"},
            1400: {"title": "Great Expectations", "author": "Charles Dickens"},
        }

        if book_id in metadata:
            return metadata[book_id]

        # Try to extract from text header
        return {"title": f"Book {book_id}", "author": "Unknown"}

    def _clean_gutenberg_text(self, text: str) -> str:
        """Remove Gutenberg header/footer boilerplate."""
        # Find start of actual content
        start_markers = [
            "*** START OF THIS PROJECT GUTENBERG",
            "*** START OF THE PROJECT GUTENBERG",
            "*END*THE SMALL PRINT",
        ]

        for marker in start_markers:
            pos = text.find(marker)
            if pos != -1:
                # Find end of line
                newline = text.find('\n', pos)
                if newline != -1:
                    text = text[newline + 1:]
                break

        # Find end of actual content
        end_markers = [
            "*** END OF THIS PROJECT GUTENBERG",
            "*** END OF THE PROJECT GUTENBERG",
            "End of the Project Gutenberg",
        ]

        for marker in end_markers:
            pos = text.find(marker)
            if pos != -1:
                text = text[:pos]
                break

        return text.strip()

    def get_documents(self) -> Generator[SourceDocument, None, None]:
        """Yield documents from Gutenberg."""
        for i, book_id in enumerate(self.book_ids[:self.max_books]):
            text = self._get_book_text(book_id)
            if not text:
                continue

            text = self._clean_gutenberg_text(text)
            metadata = self._get_book_metadata(book_id)

            yield SourceDocument(
                text=text,
                title=metadata["title"],
                author=metadata["author"],
                source_id=f"gutenberg:{book_id}"
            )
