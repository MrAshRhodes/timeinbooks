"""Cache of processed sources to avoid re-scraping."""
import os
import json
from typing import Set
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(__file__), "processed.json")


def load_processed() -> Set[str]:
    """Load set of processed source IDs."""
    if not os.path.exists(CACHE_FILE):
        return set()

    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get("processed", []))
    except (json.JSONDecodeError, IOError):
        return set()


def save_processed(processed: Set[str]):
    """Save processed source IDs."""
    data = {
        "processed": list(processed),
        "last_updated": datetime.now().isoformat()
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def mark_processed(source_id: str):
    """Mark a single source as processed."""
    processed = load_processed()
    processed.add(source_id)
    save_processed(processed)


def is_processed(source_id: str) -> bool:
    """Check if a source has been processed."""
    return source_id in load_processed()


def clear_processed():
    """Clear the processed cache."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)


def get_stats() -> dict:
    """Get cache statistics."""
    processed = load_processed()
    gutenberg_count = sum(1 for p in processed if p.startswith("gutenberg:"))
    scripts_count = sum(1 for p in processed if p.startswith("imsdb:"))

    return {
        "total": len(processed),
        "gutenberg": gutenberg_count,
        "scripts": scripts_count
    }
