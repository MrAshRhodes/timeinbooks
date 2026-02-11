"""Base class for quote sources."""
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional

import sys
sys.path.insert(0, '..')
from time_patterns import find_times, TimeMatch
from formatter import Quote, extract_quote_context
from processed_cache import ProcessedCache


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

    # Parallel download settings
    concurrency: int = 5
    request_delay: float = 0.5

    @property
    @abstractmethod
    def name(self) -> str:
        """Source name for logging."""
        pass

    @abstractmethod
    def get_documents(self) -> Generator[SourceDocument, None, None]:
        """Yield documents to process. Should be an infinite/paginated generator."""
        pass

    def get_candidate_ids(self) -> Generator[tuple, None, None]:
        """Yield (source_id, metadata_dict) for documents available to download.

        Override this to enable parallel downloading. The metadata dict should
        contain whatever the subclass needs to fetch the document content.
        """
        raise NotImplementedError

    def fetch_document(self, source_id: str, metadata: dict) -> Optional[SourceDocument]:
        """Download a single document given its source_id and metadata.

        Override this to enable parallel downloading.
        """
        raise NotImplementedError

    def _supports_parallel(self) -> bool:
        """Check if this source implements parallel download methods."""
        try:
            # Check if subclass overrode both methods
            cls = type(self)
            return (cls.get_candidate_ids is not BaseSource.get_candidate_ids and
                    cls.fetch_document is not BaseSource.fetch_document)
        except AttributeError:
            return False

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
        """Scrape documents, using parallel downloads when supported."""
        if self._supports_parallel():
            return self._scrape_parallel(skip_processed)
        return self._scrape_sequential(skip_processed)

    def _scrape_sequential(self, skip_processed: bool = True) -> Dict[str, List[Quote]]:
        """Original sequential scrape for sources that don't support parallel."""
        cache = ProcessedCache()
        cache.load()

        quotes_by_time: Dict[str, List[Quote]] = {}
        new_docs_processed = 0
        skipped_docs = 0
        total_quotes = 0

        print(f"[{self.name}] Starting scrape (target: {self.max_items} new docs)...")

        try:
            for doc in self.get_documents():
                # Skip already processed documents
                if skip_processed and cache.is_processed(doc.source_id):
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

                # Mark as processed (in-memory)
                cache.mark_processed(doc.source_id)

                # Stop when we've processed enough NEW documents
                if new_docs_processed >= self.max_items:
                    break
        finally:
            # Flush cache to disk once at the end
            cache.flush()

        if skipped_docs > 0:
            print(f"[{self.name}] Skipped {skipped_docs} already processed docs")
        print(f"[{self.name}] Complete: {new_docs_processed} new docs, {total_quotes} quotes")
        return quotes_by_time

    def _scrape_parallel(self, skip_processed: bool = True) -> Dict[str, List[Quote]]:
        """Parallel scrape using ThreadPoolExecutor for concurrent downloads."""
        cache = ProcessedCache()
        cache.load()

        quotes_by_time: Dict[str, List[Quote]] = {}
        new_docs_processed = 0
        skipped_docs = 0
        total_quotes = 0

        print(f"[{self.name}] Starting parallel scrape "
              f"(target: {self.max_items} new docs, workers: {self.concurrency})...")

        # Collect candidates that need processing
        candidates = []
        for source_id, metadata in self.get_candidate_ids():
            if skip_processed and cache.is_processed(source_id):
                skipped_docs += 1
                continue
            candidates.append((source_id, metadata))
            if len(candidates) >= self.max_items:
                break

        if skipped_docs > 0:
            print(f"[{self.name}] Skipped {skipped_docs} already processed docs")

        if not candidates:
            print(f"[{self.name}] No new documents to process")
            return quotes_by_time

        print(f"[{self.name}] Downloading {len(candidates)} documents in parallel...")

        try:
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                # Submit tasks with polite delay between submissions
                futures = {}
                for i, (source_id, metadata) in enumerate(candidates):
                    future = executor.submit(self.fetch_document, source_id, metadata)
                    futures[future] = (source_id, metadata)
                    # Polite delay between submissions (not between completions)
                    if i < len(candidates) - 1 and self.request_delay > 0:
                        time.sleep(self.request_delay)

                # Process results as they complete
                for future in as_completed(futures):
                    source_id, metadata = futures[future]
                    try:
                        doc = future.result()
                    except Exception as e:
                        print(f"[{self.name}] Error downloading {source_id}: {e}")
                        continue

                    if doc is None:
                        continue

                    new_docs_processed += 1
                    print(f"[{self.name}] Processing ({new_docs_processed}/{len(candidates)}): "
                          f"{doc.title[:50]}...")

                    quote_tuples = self.extract_quotes(doc)
                    total_quotes += len(quote_tuples)

                    for time_key, quote in quote_tuples:
                        if time_key:
                            if time_key not in quotes_by_time:
                                quotes_by_time[time_key] = []
                            quotes_by_time[time_key].append(quote)

                    # Mark as processed (in-memory)
                    cache.mark_processed(doc.source_id)
        finally:
            # Flush cache to disk once at the end
            cache.flush()

        print(f"[{self.name}] Complete: {new_docs_processed} new docs, {total_quotes} quotes")
        return quotes_by_time
