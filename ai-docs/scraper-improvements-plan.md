# Quote Scraper Improvements Plan

## Problems

### 1. Max Count Bug
When user requests `--max 200` but 96 documents are already processed:
- **Current behavior**: Fetches 200 total, skips 96, processes only 104 new
- **Expected behavior**: Keep fetching until 200 NEW documents are processed

### 2. No Progress Feedback
When merging large numbers of quotes:
- **Current behavior**: Silent processing, appears stuck
- **Expected behavior**: Progress bar showing merge status

---

## Solution

### Fix 1: Process N New Documents (Not N Total)

**Files to modify:**
- `sources/gutenberg.py`
- `sources/scripts.py`
- `sources/base.py`

**Approach:**
Change the document fetching to be a paginated generator that continues fetching until we've processed the requested number of NEW documents.

**Gutenberg changes (`sources/gutenberg.py`):**
- Remove fixed `_get_book_ids()` that returns exactly N IDs
- Add paginated `_fetch_books_paginated()` generator that yields book IDs indefinitely
- Fetch pages of books on-demand (32 per page from Gutendex API)
- Let `base.py` control when to stop based on new documents processed

**Scripts changes (`sources/scripts.py`):**
- Similar approach: paginated generator for script names
- Fetch full script list once, yield one at a time
- Let `base.py` control stopping

**Base changes (`sources/base.py`):**
- Track `new_docs_processed` counter (not total attempted)
- Continue iterating `get_documents()` until `new_docs_processed >= max_items`
- Stop early if source is exhausted (no more documents available)

### Fix 2: Add Progress Bar for Merge

**Files to modify:**
- `merger.py`
- `requirements.txt` (add `tqdm`)

**Approach:**
- Use `tqdm` library for progress bars
- Add progress bar around quote iteration in `merge_quotes()`
- Show: quotes processed, time elapsed, rate

---

## Implementation Details

### Gutenberg Source Changes

```python
# OLD: _get_book_ids() returns fixed list
# NEW: _fetch_books_paginated() is a generator

def _fetch_books_paginated(self):
    """Generator that yields book IDs, fetching pages as needed."""
    page = 1
    while True:
        url = f"https://gutendex.com/books/?page={page}&sort=popular"
        response = requests.get(url)
        if response.status_code != 200:
            break
        data = response.json()
        results = data.get('results', [])
        if not results:
            break
        for book in results:
            yield book['id']
        if not data.get('next'):
            break
        page += 1

def get_documents(self):
    """Generator that yields documents from paginated source."""
    for book_id in self._fetch_books_paginated():
        # ... existing download/parse logic ...
        yield doc
```

### Base Source Changes

```python
def scrape(self, skip_processed: bool = True) -> Dict[str, List[Quote]]:
    new_docs_processed = 0
    skipped_docs = 0

    for doc in self.get_documents():
        if skip_processed and is_processed(doc.source_id):
            skipped_docs += 1
            continue

        # Process this document
        new_docs_processed += 1
        # ... extract quotes ...
        mark_processed(doc.source_id)

        # Stop when we've processed enough NEW documents
        if new_docs_processed >= self.max_items:
            break

    print(f"[{self.name}] Skipped {skipped_docs} already processed docs")
    print(f"[{self.name}] Complete: {new_docs_processed} new docs processed")
```

### Merger Progress Bar

```python
from tqdm import tqdm

def merge_quotes(existing, new, dedupe=True):
    merged = defaultdict(list)
    duplicates = set()

    # ... existing dedup setup ...

    total_quotes = sum(len(quotes) for quotes in new.values())

    with tqdm(total=total_quotes, desc="Merging quotes", unit="quote") as pbar:
        for time_key, new_quotes in new.items():
            for quote in new_quotes:
                # ... existing merge logic ...
                pbar.update(1)

    return merged
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `sources/gutenberg.py` | Replace `_get_book_ids()` with paginated generator |
| `sources/scripts.py` | Replace `_get_script_names()` with paginated generator |
| `sources/base.py` | Track new docs processed, stop at max NEW items |
| `merger.py` | Add tqdm progress bar to merge loop |
| `requirements.txt` | Add `tqdm` dependency |

---

## Verification

1. Run `python main.py --source gutenberg --max 10` with some already processed
   - Should see: "Skipped X already processed" and "10 new docs processed"

2. Run `python main.py --source scripts --max 10` with some already processed
   - Same behavior

3. Run `python main.py --merge` with new_quotes.json containing many quotes
   - Should see progress bar with quote count and rate

4. Test edge case: Request more items than available
   - Should process all available, then stop gracefully
