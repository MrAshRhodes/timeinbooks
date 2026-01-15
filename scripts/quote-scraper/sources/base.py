"""Base class for quote sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Generator
from dataclasses import dataclass

import sys
sys.path.insert(0, '..')
from time_patterns import find_times, TimeMatch
from formatter import Quote, extract_quote_context


@dataclass
class SourceDocument:
    """A document from a source."""
    text: str
    title: str
    author: str
    source_id: str = ""


class BaseSource(ABC):
    """Abstract base class for quote sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Source name for logging."""
        pass

    @abstractmethod
    def get_documents(self) -> Generator[SourceDocument, None, None]:
        """Yield documents to process."""
        pass

    def extract_quotes(self, doc: SourceDocument) -> List[Quote]:
        """Extract quotes from a document."""
        quotes = []
        matches = find_times(doc.text)

        for match in matches:
            quote = extract_quote_context(doc.text, match)
            if quote:
                quote.title = doc.title
                quote.author = doc.author
                quotes.append(quote)

        return quotes

    def scrape(self) -> Dict[str, List[Quote]]:
        """Scrape all documents and return quotes by time."""
        quotes_by_time: Dict[str, List[Quote]] = {}
        total_docs = 0
        total_quotes = 0

        print(f"[{self.name}] Starting scrape...")

        for doc in self.get_documents():
            total_docs += 1
            print(f"[{self.name}] Processing: {doc.title[:50]}...")

            quotes = self.extract_quotes(doc)
            total_quotes += len(quotes)

            for quote in quotes:
                time_key = None
                # Find the time key from the original match
                matches = find_times(
                    quote.quote_first + quote.quote_time_case + quote.quote_last
                )
                if matches:
                    time_key = matches[0].time_24h

                if time_key:
                    if time_key not in quotes_by_time:
                        quotes_by_time[time_key] = []
                    quotes_by_time[time_key].append(quote)

        print(f"[{self.name}] Complete: {total_docs} docs, {total_quotes} quotes")
        return quotes_by_time
