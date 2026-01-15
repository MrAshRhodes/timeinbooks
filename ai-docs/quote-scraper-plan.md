# Quote Scraping Utility Plan

## Overview
Create a standalone utility to find and extract new quotes containing time references for the literary quote clock. Run monthly to expand the quote database.

---

## Quote Format Required

```javascript
{
  "quote_first": "text before the time",
  "quote_time_case": "the time as written (e.g., 'midnight', '3:45', 'seven o'clock')",
  "quote_last": "text after the time",
  "title": "Source title",
  "author": "Author name",
  "sfw": "yes"
}
```

Keyed by 24-hour time: `"HH:MM"`

---

## Approach Options

### 1. Public Domain Book Scraping (Recommended)

**Sources:**
- **Project Gutenberg** - 70,000+ free ebooks (gutenberg.org)
- **Standard Ebooks** - Curated, well-formatted public domain books
- **Internet Archive** - Millions of texts

**Method:**
```python
# Pseudocode
1. Download book text files
2. Regex search for time patterns:
   - Digital: r'\b(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?\b'
   - Words: r'\b(one|two|...|twelve)\s+o\'clock\b'
   - Named: r'\b(midnight|noon|midday)\b'
   - Phrases: r'\b(quarter past|half past|quarter to)\s+(one|two|...)\b'
3. Extract ~100 chars before and after match
4. Map to 24-hour format
5. Store with book metadata
```

**Pros:** Legal, large corpus, known authors
**Cons:** Older language style, limited contemporary quotes

---

### 2. Wikiquote Scraping

**Source:** wikiquote.org

**Method:**
- Scrape quote pages by author/work
- Search for time references
- Extract with attribution

**Pros:** Pre-curated quotes, good attribution
**Cons:** Smaller corpus, may miss context

---

### 3. AI-Assisted Extraction

**Method:**
```python
# Use Claude API to process text chunks
prompt = """
Find quotes containing specific times in this text.
For each quote found, extract:
- The time mentioned (map to HH:MM 24h format)
- Text before the time
- The time as written
- Text after the time
Return as JSON.
"""
```

**Pros:** Better context extraction, handles complex time references
**Cons:** API costs, rate limits

---

### 4. Movie/TV Script Mining

**Sources:**
- IMSDb (movie scripts)
- TV transcripts

**Method:** Same regex approach on dialogue

**Pros:** Contemporary language, diverse content
**Cons:** Less "literary", attribution complexity

---

### 5. Song Lyrics

**Sources:**
- Genius API
- AZLyrics

**Method:** Search lyrics databases for time references

**Pros:** Lots of time references in songs
**Cons:** Copyright concerns, may not fit "literary" theme

---

## Recommended Implementation (Multi-Source)

### Project Structure

```
scripts/
  quote-scraper/
    main.py              # CLI entry point
    sources/
      __init__.py
      gutenberg.py       # Project Gutenberg scraper
      scripts.py         # Movie/TV script scraper
      base.py            # Base scraper class
    ai_extractor.py      # Claude API for context extraction
    time_patterns.py     # Regex patterns for time detection
    formatter.py         # Convert to quote format
    merger.py            # Merge into quotes.js
    deduper.py           # Remove duplicates
    config.py            # Settings & API keys
    requirements.txt
    README.md
```

### Dependencies

```
requests
beautifulsoup4
gutenbergpy
anthropic
python-dotenv
```

### Phase 1: Core Infrastructure
- Time pattern detection (regex)
- Quote formatter (to JSON structure)
- Base scraper class

### Phase 2: Project Gutenberg Source
- Download popular/classic books
- Extract time-referenced passages
- Map to 24h format

### Phase 3: Script Source
- Scrape IMSDb movie scripts
- Process dialogue for time references
- Handle attribution (movie title, year)

### Phase 4: AI Enhancement
- Use Claude to refine extracted quotes
- Better context boundaries
- Handle ambiguous time references (AM/PM)
- Filter low-quality extractions

### Phase 5: Merger & Deduplication
- Merge new quotes into quotes.js
- Deduplicate by text similarity
- Validate format
- Generate updated quotes.js

---

## Time Pattern Mappings

| Pattern | 24h Format |
|---------|------------|
| midnight | 00:00 |
| 1 AM, one in the morning | 01:00 |
| noon, midday | 12:00 |
| 1 PM, one in the afternoon | 13:00 |
| quarter past three | 03:15 or 15:15 |
| half past seven | 07:30 or 19:30 |
| quarter to nine | 08:45 or 20:45 |

---

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/quote-scraper/scraper.py` | Main entry point |
| `scripts/quote-scraper/time_patterns.py` | Regex patterns |
| `scripts/quote-scraper/formatter.py` | Output formatting |
| `scripts/quote-scraper/requirements.txt` | Dependencies |
| `scripts/quote-scraper/README.md` | Usage docs |

---

## Verification

1. Run scraper on a small test corpus (1-2 books)
2. Verify extracted quotes have correct time mappings
3. Check quote context is meaningful
4. Merge into quotes.js and test in app
5. Verify no duplicates with existing quotes
