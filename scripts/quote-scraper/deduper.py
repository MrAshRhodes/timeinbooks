"""Quote deduplication utilities."""
import sys
from typing import List, Dict, Set
from difflib import SequenceMatcher

from tqdm import tqdm

from formatter import Quote


def similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def get_quote_text(quote: Quote | dict) -> str:
    """Get full quote text for comparison."""
    if isinstance(quote, dict):
        return f"{quote['quote_first']}{quote['quote_time_case']}{quote['quote_last']}"
    return f"{quote.quote_first}{quote.quote_time_case}{quote.quote_last}"


def dedupe_quotes(quotes: List[Quote | dict], threshold: float = 0.85) -> List[Quote | dict]:
    """Remove duplicate or near-duplicate quotes."""
    if not quotes:
        return []

    unique = [quotes[0]]

    for quote in quotes[1:]:
        quote_text = get_quote_text(quote)
        is_duplicate = False

        for existing in unique:
            existing_text = get_quote_text(existing)
            if similarity(quote_text, existing_text) >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(quote)

    return unique


def dedupe_by_time(quotes_by_time: Dict[str, List]) -> Dict[str, List]:
    """Deduplicate quotes within each time slot."""
    result = {}
    sys.stdout.flush()

    for time_key, quotes in tqdm(quotes_by_time.items(), desc="Deduplicating", unit="slot"):
        result[time_key] = dedupe_quotes(quotes)

    return result


def find_duplicates_across_sources(
    existing: Dict[str, List],
    new: Dict[str, List],
    threshold: float = 0.85
) -> Set[str]:
    """Find quotes in 'new' that are duplicates of 'existing'."""
    duplicate_texts = set()

    # Count total new quotes for progress bar
    total_new = sum(len(quotes) for quotes in new.values())
    sys.stdout.flush()

    with tqdm(total=total_new, desc="Checking duplicates", unit="quote") as pbar:
        for time_key, new_quotes in new.items():
            existing_quotes = existing.get(time_key, [])

            for new_quote in new_quotes:
                new_text = get_quote_text(new_quote)

                for existing_quote in existing_quotes:
                    existing_text = get_quote_text(existing_quote)
                    if similarity(new_text, existing_text) >= threshold:
                        duplicate_texts.add(new_text)
                        break

                pbar.update(1)

    return duplicate_texts
