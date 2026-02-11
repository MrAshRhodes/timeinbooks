"""Quote deduplication utilities."""
import sys
from typing import List, Dict, Set

from rapidfuzz import fuzz
from tqdm import tqdm

from formatter import Quote


def _quick_reject(a: str, b: str, threshold: float) -> bool:
    """Fast check to reject obvious non-duplicates before expensive similarity.

    Returns True if the strings are definitely NOT similar enough (safe to skip).
    Returns False if we can't rule out similarity (must run full comparison).
    """
    # Length difference > 30% means similarity can't reach typical thresholds
    len_a, len_b = len(a), len(b)
    if len_a == 0 or len_b == 0:
        return len_a != len_b
    ratio = len_a / len_b if len_a < len_b else len_b / len_a
    if ratio < 0.7:
        return True

    # Check if first 20 characters have any overlap (case-insensitive)
    prefix_a = set(a[:20].lower())
    prefix_b = set(b[:20].lower())
    if not prefix_a & prefix_b:
        return True

    return False


def similarity(a: str, b: str, threshold: float = 0.85) -> float:
    """Calculate string similarity ratio using rapidfuzz with early-exit optimization."""
    if _quick_reject(a, b, threshold):
        return 0.0
    return fuzz.ratio(a.lower(), b.lower()) / 100.0


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
    # Pre-compute texts to avoid repeated concatenation
    unique_texts = [get_quote_text(quotes[0])]

    for quote in quotes[1:]:
        quote_text = get_quote_text(quote)
        is_duplicate = False

        for existing_text in unique_texts:
            if similarity(quote_text, existing_text) >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(quote)
            unique_texts.append(quote_text)

    return unique


def dedupe_by_time(quotes_by_time: Dict[str, List]) -> Dict[str, List]:
    """Deduplicate quotes within each time slot."""
    result = {}
    sys.stdout.flush()

    # Count total quotes for more accurate progress
    total_quotes = sum(len(quotes) for quotes in quotes_by_time.values())

    with tqdm(total=total_quotes, desc="Deduplicating", unit="quote") as pbar:
        for time_key, quotes in quotes_by_time.items():
            result[time_key] = dedupe_quotes(quotes)
            pbar.update(len(quotes))

    return result


def find_duplicates_across_sources(
    existing: Dict[str, List],
    new: Dict[str, List],
    threshold: float = 0.85
) -> Set[str]:
    """Find quotes in 'new' that are duplicates of 'existing'."""
    duplicate_texts = set()

    # Pre-compute existing quote texts per time slot to avoid repeated concatenation
    existing_texts_by_time: Dict[str, List[str]] = {}
    for time_key, quotes in existing.items():
        existing_texts_by_time[time_key] = [get_quote_text(q) for q in quotes]

    # Count total new quotes for progress bar
    total_new = sum(len(quotes) for quotes in new.values())
    sys.stdout.flush()

    with tqdm(total=total_new, desc="Checking duplicates", unit="quote") as pbar:
        for time_key, new_quotes in new.items():
            existing_texts = existing_texts_by_time.get(time_key, [])

            for new_quote in new_quotes:
                new_text = get_quote_text(new_quote)

                for existing_text in existing_texts:
                    if similarity(new_text, existing_text) >= threshold:
                        duplicate_texts.add(new_text)
                        break

                pbar.update(1)

    return duplicate_texts
