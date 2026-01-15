"""Project Gutenberg quote source."""
import os
import re
import json
from typing import Generator, List, Optional, Dict

import requests

import sys
sys.path.insert(0, '..')
from config import GUTENBERG_CACHE_DIR
from .base import BaseSource, SourceDocument


# Fallback popular books if API fails
FALLBACK_BOOK_IDS = [
    1342, 84, 1661, 11, 98, 2701, 1952, 174, 345, 16328,
    100, 1232, 76, 74, 1400, 55, 1080, 46, 5200, 1260,
]


class GutenbergSource(BaseSource):
    """Scrape quotes from Project Gutenberg books."""

    GUTENBERG_MIRROR = "https://www.gutenberg.org"
    GUTENDEX_API = "https://gutendex.com/books"

    def __init__(self, book_ids: Optional[List[int]] = None, max_books: int = 50):
        self.book_ids = book_ids
        self.max_books = max_books
        self._metadata_cache: Dict[int, dict] = {}
        os.makedirs(GUTENBERG_CACHE_DIR, exist_ok=True)

    @property
    def name(self) -> str:
        return "Gutenberg"

    def _fetch_popular_books(self, count: int) -> List[int]:
        """Fetch popular book IDs from Gutendex API."""
        book_ids = []
        page = 1

        print(f"  Fetching top {count} books from Gutenberg catalog...")

        while len(book_ids) < count:
            try:
                # Gutendex returns books sorted by popularity by default
                url = f"{self.GUTENDEX_API}?page={page}&languages=en"
                response = requests.get(url, timeout=30)

                if response.status_code != 200:
                    break

                data = response.json()
                results = data.get("results", [])

                if not results:
                    break

                for book in results:
                    book_id = book.get("id")
                    if book_id and book_id not in book_ids:
                        # Cache metadata while we have it
                        authors = book.get("authors", [])
                        author = authors[0].get("name", "Unknown") if authors else "Unknown"
                        self._metadata_cache[book_id] = {
                            "title": book.get("title", f"Book {book_id}"),
                            "author": author
                        }
                        book_ids.append(book_id)

                        if len(book_ids) >= count:
                            break

                page += 1

                # Safety limit
                if page > 20:
                    break

            except Exception as e:
                print(f"  Warning: API error: {e}")
                break

        print(f"  Found {len(book_ids)} books from catalog")
        return book_ids

    def _get_book_ids(self) -> List[int]:
        """Get book IDs to process."""
        if self.book_ids:
            return self.book_ids[:self.max_books]

        # Try to fetch from API
        ids = self._fetch_popular_books(self.max_books)

        # Fall back to hardcoded if API fails
        if len(ids) < self.max_books:
            for fallback_id in FALLBACK_BOOK_IDS:
                if fallback_id not in ids:
                    ids.append(fallback_id)
                if len(ids) >= self.max_books:
                    break

        return ids[:self.max_books]

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

        return None

    def _extract_metadata_from_text(self, text: str, book_id: int) -> dict:
        """Extract title and author from Gutenberg text header."""
        title = f"Book {book_id}"
        author = "Unknown"

        # Look for title
        title_match = re.search(r'Title:\s*(.+?)(?:\r?\n|$)', text[:2000])
        if title_match:
            title = title_match.group(1).strip()

        # Look for author
        author_match = re.search(r'Author:\s*(.+?)(?:\r?\n|$)', text[:2000])
        if author_match:
            author = author_match.group(1).strip()

        return {"title": title, "author": author}

    def _get_book_metadata(self, book_id: int, text: str = "") -> dict:
        """Get book metadata from cache, API result, or text extraction."""
        # Check cache first (populated during API fetch)
        if book_id in self._metadata_cache:
            return self._metadata_cache[book_id]

        # Try to extract from text
        if text:
            metadata = self._extract_metadata_from_text(text, book_id)
            self._metadata_cache[book_id] = metadata
            return metadata

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
        book_ids = self._get_book_ids()

        for book_id in book_ids:
            raw_text = self._get_book_text(book_id)
            if not raw_text:
                continue

            # Get metadata before cleaning (header contains metadata)
            metadata = self._get_book_metadata(book_id, raw_text)
            text = self._clean_gutenberg_text(raw_text)

            yield SourceDocument(
                text=text,
                title=metadata["title"],
                author=metadata["author"],
                source_id=f"gutenberg:{book_id}"
            )
