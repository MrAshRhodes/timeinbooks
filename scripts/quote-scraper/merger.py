"""Merge new quotes into existing quotes.js."""
import re
import json
from typing import Dict, List

from config import QUOTES_FILE, NEW_QUOTES_FILE
from formatter import Quote, format_quotes_js
from deduper import dedupe_by_time, find_duplicates_across_sources, get_quote_text


def load_existing_quotes() -> Dict[str, List[dict]]:
    """Load existing quotes from quotes.js."""
    try:
        with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract the QUOTES object
        match = re.search(r'const QUOTES = ({[\s\S]*});', content)
        if not match:
            print("Warning: Could not parse existing quotes.js")
            return {}

        # Parse as JSON (need to handle trailing commas)
        json_str = match.group(1)
        # Remove trailing commas before ] and }
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        return json.loads(json_str)

    except FileNotFoundError:
        print("No existing quotes.js found, starting fresh")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing quotes.js: {e}")
        return {}


def save_new_quotes(quotes: Dict[str, List]) -> str:
    """Save new quotes to JSON file for review."""
    output = {}
    for time_key, quote_list in quotes.items():
        output[time_key] = [
            q.to_dict() if isinstance(q, Quote) else q
            for q in quote_list
        ]

    with open(NEW_QUOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    return NEW_QUOTES_FILE


def merge_quotes(
    existing: Dict[str, List],
    new: Dict[str, List],
    dedupe: bool = True
) -> Dict[str, List]:
    """Merge new quotes into existing, optionally deduplicating."""
    merged = {k: list(v) for k, v in existing.items()}

    # Find duplicates first
    if dedupe:
        duplicates = find_duplicates_across_sources(existing, new)
        print(f"Found {len(duplicates)} duplicate quotes to skip")

    added_count = 0
    for time_key, new_quotes in new.items():
        if time_key not in merged:
            merged[time_key] = []

        for quote in new_quotes:
            quote_text = get_quote_text(quote)

            if dedupe and quote_text in duplicates:
                continue

            quote_dict = quote.to_dict() if isinstance(quote, Quote) else quote
            merged[time_key].append(quote_dict)
            added_count += 1

    print(f"Added {added_count} new quotes")

    # Final deduplication within time slots
    if dedupe:
        merged = dedupe_by_time(merged)

    return merged


def write_quotes_js(quotes: Dict[str, List]) -> str:
    """Write merged quotes to quotes.js."""
    content = format_quotes_js(quotes)

    with open(QUOTES_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    return QUOTES_FILE


def run_merge(new_quotes: Dict[str, List], dry_run: bool = False) -> Dict[str, List]:
    """Full merge workflow."""
    print("Loading existing quotes...")
    existing = load_existing_quotes()
    print(f"Loaded {sum(len(v) for v in existing.values())} existing quotes")

    print("Merging quotes...")
    merged = merge_quotes(existing, new_quotes)
    print(f"Total quotes after merge: {sum(len(v) for v in merged.values())}")

    if dry_run:
        print("Dry run - saving to new_quotes.json for review")
        path = save_new_quotes(new_quotes)
        print(f"Saved to {path}")
    else:
        print("Writing quotes.js...")
        path = write_quotes_js(merged)
        print(f"Saved to {path}")

    return merged
