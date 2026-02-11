"""Tests for deduper.py - similarity threshold, edge cases, optimization correctness."""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deduper import similarity, _quick_reject, get_quote_text, dedupe_quotes, dedupe_by_time, find_duplicates_across_sources
from formatter import Quote


# --- Helper to create quotes ---

def make_quote(first, time, last, title="Book", author="Author"):
    return Quote(
        quote_first=first,
        quote_time_case=time,
        quote_last=last,
        title=title,
        author=author
    )


def make_dict_quote(first, time, last, title="Book", author="Author"):
    return {
        "quote_first": first,
        "quote_time_case": time,
        "quote_last": last,
        "title": title,
        "author": author,
        "sfw": "yes"
    }


# --- _quick_reject tests ---

class TestQuickReject:
    def test_very_different_lengths_rejected(self):
        assert _quick_reject("short", "this is a much much longer string", 0.85) is True

    def test_similar_lengths_not_rejected(self):
        assert _quick_reject("hello world", "hello there", 0.85) is False

    def test_no_prefix_overlap_rejected(self):
        # Completely different first 20 chars, but same length
        a = "abcdefghijklmnopqrst"
        b = "12345678901234567890"
        assert _quick_reject(a, b, 0.85) is True

    def test_prefix_overlap_not_rejected(self):
        a = "the quick brown fox"
        b = "the quick red fox"
        assert _quick_reject(a, b, 0.85) is False

    def test_empty_strings_equal(self):
        assert _quick_reject("", "", 0.85) is False

    def test_one_empty_rejected(self):
        assert _quick_reject("hello", "", 0.85) is True
        assert _quick_reject("", "hello", 0.85) is True

    def test_length_ratio_boundary(self):
        # 7 chars vs 10 chars = 0.7 ratio, borderline
        a = "abcdefg"
        b = "abcdefghij"
        assert _quick_reject(a, b, 0.85) is False  # exactly 0.7, not < 0.7

    def test_length_ratio_just_below_boundary(self):
        # 6 chars vs 10 chars = 0.6 ratio, should reject
        a = "abcdef"
        b = "abcdefghij"
        assert _quick_reject(a, b, 0.85) is True


# --- similarity tests ---

class TestSimilarity:
    def test_identical_strings(self):
        assert similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        score = similarity("abcdefghijklmnopqrst", "12345678901234567890")
        assert score == 0.0  # Quick reject kicks in

    def test_similar_strings_high_score(self):
        score = similarity(
            "The clock struck twelve and the bell rang",
            "The clock struck twelve and the bell tolled"
        )
        assert score > 0.8

    def test_case_insensitive(self):
        assert similarity("Hello World", "hello world") == 1.0

    def test_very_different_lengths_returns_zero(self):
        score = similarity("hi", "this is a very long string indeed")
        assert score == 0.0  # Quick reject due to length

    def test_empty_strings(self):
        # Both empty: _quick_reject returns False (lengths equal),
        # rapidfuzz.fuzz.ratio("","") returns 100.0 (perfect match)
        result = similarity("", "")
        assert result == 1.0

    def test_quick_reject_preserves_dedup_results(self):
        """Verify that quick_reject doesn't change dedup outcomes for similar strings."""
        from rapidfuzz import fuzz

        pairs = [
            ("The cat sat on the mat", "The cat sat on a mat"),
            ("It was midnight when he arrived", "It was midnight when she arrived"),
            ("Quarter past seven the bell rang", "Quarter past seven the bell tolled"),
        ]
        for a, b in pairs:
            optimized = similarity(a, b)
            raw = fuzz.ratio(a.lower(), b.lower()) / 100.0
            assert abs(optimized - raw) < 0.001, f"Mismatch for {a!r} vs {b!r}"


# --- get_quote_text tests ---

class TestGetQuoteText:
    def test_with_quote_object(self):
        q = make_quote("Before ", "noon", " after")
        assert get_quote_text(q) == "Before noon after"

    def test_with_dict(self):
        d = make_dict_quote("Before ", "noon", " after")
        assert get_quote_text(d) == "Before noon after"

    def test_empty_parts(self):
        q = make_quote("", "midnight", "")
        assert get_quote_text(q) == "midnight"


# --- dedupe_quotes tests ---

class TestDedupeQuotes:
    def test_empty_list(self):
        assert dedupe_quotes([]) == []

    def test_single_quote(self):
        q = make_quote("The clock struck ", "noon", " and all was well.")
        result = dedupe_quotes([q])
        assert len(result) == 1

    def test_identical_quotes_deduped(self):
        q1 = make_quote("The clock struck ", "noon", " and all was well.")
        q2 = make_quote("The clock struck ", "noon", " and all was well.")
        result = dedupe_quotes([q1, q2])
        assert len(result) == 1

    def test_similar_quotes_deduped(self):
        q1 = make_quote("The old clock struck ", "noon", " and the town was quiet.")
        q2 = make_quote("The old clock struck ", "noon", " and the town grew quiet.")
        result = dedupe_quotes([q1, q2])
        assert len(result) == 1  # Similar enough to dedupe

    def test_different_quotes_kept(self):
        q1 = make_quote("The sun rose at ", "dawn", " over the mountains.")
        q2 = make_quote("The submarine surfaced at ", "midnight", " near the coast.")
        result = dedupe_quotes([q1, q2])
        assert len(result) == 2

    def test_custom_threshold(self):
        q1 = make_quote("The clock struck ", "noon", " in the tower.")
        q2 = make_quote("The clock chimed ", "noon", " in the hall.")
        # With very high threshold, these should be kept as separate
        result_strict = dedupe_quotes([q1, q2], threshold=0.99)
        assert len(result_strict) == 2

    def test_preserves_first_of_duplicates(self):
        q1 = make_quote("First version at ", "noon", " here.", title="Book A")
        q2 = make_quote("First version at ", "noon", " here.", title="Book B")
        result = dedupe_quotes([q1, q2])
        assert len(result) == 1
        assert result[0].title == "Book A"

    def test_works_with_dicts(self):
        d1 = make_dict_quote("The clock struck ", "noon", " and all was well.")
        d2 = make_dict_quote("The clock struck ", "noon", " and all was well.")
        result = dedupe_quotes([d1, d2])
        assert len(result) == 1

    def test_mixed_quotes_and_dicts(self):
        q1 = make_quote("The clock struck ", "noon", " and all was well.")
        d1 = make_dict_quote("Something completely different at ", "midnight", " occurred.")
        result = dedupe_quotes([q1, d1])
        assert len(result) == 2


# --- dedupe_by_time tests ---

class TestDedupeByTime:
    def test_empty_dict(self):
        result = dedupe_by_time({})
        assert result == {}

    def test_single_time_slot(self):
        q1 = make_quote("A ", "noon", " B")
        q2 = make_quote("A ", "noon", " B")  # duplicate
        q3 = make_quote("Completely different text at ", "noon", " with unique ending.")
        result = dedupe_by_time({"12:00": [q1, q2, q3]})
        assert "12:00" in result
        assert len(result["12:00"]) == 2  # q1 kept, q2 deduped, q3 kept

    def test_multiple_time_slots(self):
        q1 = make_quote("Morning ", "seven o'clock", " routine.")
        q2 = make_quote("Evening ", "midnight", " silence.")
        result = dedupe_by_time({
            "07:00": [q1],
            "00:00": [q2]
        })
        assert len(result) == 2
        assert len(result["07:00"]) == 1
        assert len(result["00:00"]) == 1


# --- find_duplicates_across_sources tests ---

class TestFindDuplicatesAcrossSources:
    def test_finds_exact_duplicates(self):
        existing = {"12:00": [make_quote("The clock struck ", "noon", " and all was well.")]}
        new = {"12:00": [make_quote("The clock struck ", "noon", " and all was well.")]}
        dupes = find_duplicates_across_sources(existing, new)
        assert len(dupes) == 1

    def test_no_duplicates(self):
        existing = {"12:00": [make_quote("First quote at ", "noon", " here.")]}
        new = {"12:00": [make_quote("Completely different text at ", "noon", " with unique words.")]}
        dupes = find_duplicates_across_sources(existing, new)
        assert len(dupes) == 0

    def test_different_time_slots_no_cross_match(self):
        existing = {"12:00": [make_quote("The clock struck ", "noon", " and all was well.")]}
        new = {"00:00": [make_quote("The clock struck ", "noon", " and all was well.")]}
        # Different time keys, so no comparison happens
        dupes = find_duplicates_across_sources(existing, new)
        assert len(dupes) == 0

    def test_empty_existing(self):
        new = {"12:00": [make_quote("Some quote at ", "noon", " here.")]}
        dupes = find_duplicates_across_sources({}, new)
        assert len(dupes) == 0

    def test_empty_new(self):
        existing = {"12:00": [make_quote("Some quote at ", "noon", " here.")]}
        dupes = find_duplicates_across_sources(existing, {})
        assert len(dupes) == 0

    def test_custom_threshold(self):
        existing = {"12:00": [make_quote("The clock struck ", "noon", " in the tower.")]}
        new = {"12:00": [make_quote("The clock chimed ", "noon", " in the hall.")]}
        # With strict threshold, should not find duplicates
        dupes = find_duplicates_across_sources(existing, new, threshold=0.99)
        assert len(dupes) == 0


# --- Optimization correctness tests ---

class TestOptimizationCorrectness:
    """Verify that the quick_reject + rapidfuzz pipeline produces correct dedup results."""

    def test_dedupe_correctness(self):
        """Run dedupe and verify expected behavior with near-duplicates and distinct quotes."""
        quotes = [
            make_quote("The clock struck ", "noon", " and all was well."),
            make_quote("The clock struck ", "noon", " and all was fine."),  # near-dupe
            make_quote("At the stroke of ", "midnight", " the door opened."),
            make_quote("She arrived at ", "three o'clock", " looking tired."),
            make_quote("She arrived at ", "three o'clock", " looking weary."),  # near-dupe
            make_quote("Dawn broke over the mountains at ", "six", " with golden light."),
        ]

        result = dedupe_quotes(quotes, threshold=0.85)

        # We expect ~4 unique quotes (2 pairs of near-dupes collapsed, 2 distinct)
        result_texts = [get_quote_text(q) for q in result]
        assert len(result) == 4, f"Expected 4 unique quotes, got {len(result)}: {result_texts}"

        # Verify the first of each duplicate pair is preserved
        assert result[0].quote_last == " and all was well."  # first of pair 1
        assert any("midnight" in get_quote_text(q) for q in result)
        assert result[2].quote_last == " looking tired."  # first of pair 2
        assert any("golden light" in get_quote_text(q) for q in result)

    def test_quick_reject_does_not_miss_similar_pairs(self):
        """Verify quick_reject doesn't incorrectly filter out actual near-duplicates."""
        from rapidfuzz import fuzz

        pairs = [
            ("The cat sat on the mat", "The cat sat on a mat"),
            ("It was midnight when he arrived", "It was midnight when she arrived"),
            ("Quarter past seven the bell rang", "Quarter past seven the bell tolled"),
        ]
        for a, b in pairs:
            optimized = similarity(a, b)
            raw = fuzz.ratio(a.lower(), b.lower()) / 100.0
            assert abs(optimized - raw) < 0.001, (
                f"Quick reject changed similarity for similar strings!\n"
                f"Optimized: {optimized}, Raw: {raw} for {a!r} vs {b!r}"
            )
