# Plan: Remove Bible Quotes from Database

## Goal
Remove Bible quotes from `quotes.js` and prevent the scraper from collecting them in the future, to improve inclusivity.

## Changes

### 1. Update `quotes.js` - Remove existing Bible quotes
**File**: `/Users/ashley.rhodes/proj/scripts/learning-projects/vibe-quote-clock/quotes.js`

- Remove all quotes where `title === "The King James Version of the Bible"`
- This will remove ~14,676 quotes (approximately 50% of current database)
- Create a Node.js script to filter and regenerate the file

### 2. Update Gutenberg scraper - Block Bible books
**File**: `/Users/ashley.rhodes/proj/scripts/learning-projects/vibe-quote-clock/scripts/quote-scraper/sources/gutenberg.py`

Add filtering to exclude Bible-related books:
- Add `EXCLUDED_TITLES` list containing "Bible" patterns
- Add `EXCLUDED_BOOK_IDS` set containing known Bible book IDs (e.g., 10 = King James Bible)
- Filter in `_fetch_books_paginated()` to skip matching books
- Log when Bible books are skipped

### 3. No changes to IMSDb scraper
**File**: `/Users/ashley.rhodes/proj/scripts/learning-projects/vibe-quote-clock/scripts/quote-scraper/sources/scripts.py`

Films are OK - no changes needed.

## Implementation Details

### Bible identification patterns
```python
EXCLUDED_TITLES = [
    "bible",
    "king james",
    "old testament",
    "new testament",
]

EXCLUDED_BOOK_IDS = {10}  # King James Bible
```

### Quote filtering script (one-time cleanup)
```javascript
// Filter out Bible quotes from existing database
const filtered = {};
for (const [time, quotes] of Object.entries(QUOTES)) {
    filtered[time] = quotes.filter(q =>
        q.title !== "The King James Version of the Bible"
    );
}
```

## Verification
1. Run the filtering script and check new quote count (~14,662 remaining)
2. Grep quotes.js for "Bible" to confirm removal
3. Run scraper with `--max 5` to verify Bible books are skipped
4. Check scraper logs for "Skipping Bible" messages

## Files to Modify
- `quotes.js` - filter out existing Bible quotes
- `scripts/quote-scraper/sources/gutenberg.py` - add exclusion logic
