"""Base class for quote sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Generator
from dataclasses import dataclass

import sys
sys.path.insert(0, '..')
from time_patterns import find_times, TimeMatch
from formatter import Quote, extract_quote_context
from processed_cache import is_processed, mark_processed


@dataclass
class SourceDocument:
    """A document from a source."""
    text: str
    title: str
    author: str
    source_id: str = ""


class BaseSource(ABC):
    """Abstract base class for quote sources."""

    # Subclasses should set this to control how many NEW docs to process
    max_items: int = 50

    @property
    @abstractmethod
    def name(self) -> str:
        """Source name for logging."""
        pass

    @abstractmethod
    def get_documents(self) -> Generator[SourceDocument, None, None]:
        """Yield documents to process. Should be an infinite/paginated generator."""
        pass

    def extract_quotes(self, doc: SourceDocument) -> List[tuple]:
        """Extract quotes from a document. Returns list of (time_key, Quote) tuples."""
        quotes = []
        matches = find_times(doc.text)

        for match in matches:
            quote = extract_quote_context(doc.text, match)
            if quote:
                quote.title = doc.title
                quote.author = doc.author
                quotes.append((match.time_24h, quote))

        return quotes

    def scrape(self, skip_processed: bool = True) -> Dict[str, List[Quote]]:
        """Scrape documents until max_items NEW documents are processed."""
        quotes_by_time: Dict[str, List[Quote]] = {}
        new_docs_processed = 0
        skipped_docs = 0
        total_quotes = 0

        print(f"[{self.name}] Starting scrape (target: {self.max_items} new docs)...")

        for doc in self.get_documents():
            # Skip already processed documents
            if skip_processed and is_processed(doc.source_id):
                skipped_docs += 1
                continue

            new_docs_processed += 1
            print(f"[{self.name}] Processing ({new_docs_processed}/{self.max_items}): {doc.title[:50]}...")

            quote_tuples = self.extract_quotes(doc)
            total_quotes += len(quote_tuples)

            for time_key, quote in quote_tuples:
                if time_key:
                    if time_key not in quotes_by_time:
                        quotes_by_time[time_key] = []
                    quotes_by_time[time_key].append(quote)

            # Mark as processed
            mark_processed(doc.source_id)

            # Stop when we've processed enough NEW documents
            if new_docs_processed >= self.max_items:
                break

        if skipped_docs > 0:
            print(f"[{self.name}] Skipped {skipped_docs} already processed docs")
        print(f"[{self.name}] Complete: {new_docs_processed} new docs, {total_quotes} quotes")
        return quotes_by_time
