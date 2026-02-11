"""Cache of processed sources to avoid re-scraping."""
import os
import json
from typing import Set
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(__file__), "processed.json")


def _load_from_disk() -> Set[str]:
    """Load set of processed source IDs from disk."""
    if not os.path.exists(CACHE_FILE):
        return set()

    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get("processed", []))
    except (json.JSONDecodeError, IOError):
        return set()


def _save_to_disk(processed: Set[str]):
    """Save processed source IDs to disk."""
    data = {
        "processed": list(processed),
        "last_updated": datetime.now().isoformat()
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


class ProcessedCache:
    """In-memory cache that loads once and flushes to disk on demand.

    Use this instead of the module-level functions when processing multiple
    documents to avoid repeated disk I/O on every mark_processed() call.
    """

    def __init__(self):
        self._processed: Set[str] = set()
        self._dirty = False
        self._loaded = False

    def load(self):
        """Load processed IDs from disk into memory."""
        self._processed = _load_from_disk()
        self._dirty = False
        self._loaded = True

    def is_processed(self, source_id: str) -> bool:
        """Check if a source has been processed (in-memory lookup)."""
        if not self._loaded:
            self.load()
        return source_id in self._processed

    def mark_processed(self, source_id: str):
        """Mark a source as processed (in-memory only, call flush() to persist)."""
        if not self._loaded:
            self.load()
        self._processed.add(source_id)
        self._dirty = True

    def flush(self):
        """Write accumulated changes to disk (single I/O operation)."""
        if self._dirty:
            _save_to_disk(self._processed)
            self._dirty = False

    @property
    def processed(self) -> Set[str]:
        if not self._loaded:
            self.load()
        return self._processed


# --- Backward-compatible module-level functions ---

def load_processed() -> Set[str]:
    """Load set of processed source IDs."""
    return _load_from_disk()


def save_processed(processed: Set[str]):
    """Save processed source IDs."""
    _save_to_disk(processed)


def mark_processed(source_id: str):
    """Mark a single source as processed."""
    processed = _load_from_disk()
    processed.add(source_id)
    _save_to_disk(processed)


def is_processed(source_id: str) -> bool:
    """Check if a source has been processed."""
    return source_id in _load_from_disk()


def clear_processed():
    """Clear the processed cache."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)


def get_stats() -> dict:
    """Get cache statistics."""
    processed = _load_from_disk()
    gutenberg_count = sum(1 for p in processed if p.startswith("gutenberg:"))
    scripts_count = sum(1 for p in processed if p.startswith("imsdb:"))

    return {
        "total": len(processed),
        "gutenberg": gutenberg_count,
        "scripts": scripts_count
    }
