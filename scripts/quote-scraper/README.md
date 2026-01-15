# Quote Scraper

A utility to find and extract quotes containing time references from literature and movie scripts. Designed to run monthly to expand the quote database for the Literary Quote Clock.

---

## Quick Start

```bash
cd scripts/quote-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run a test scrape
python main.py --source gutenberg --max 5
```

---

## Features

- **Dynamic Source Discovery** — Automatically fetches available books/scripts from APIs
- **Smart Caching** — Tracks processed sources to avoid re-scraping
- **Time Pattern Detection** — Finds various time formats in text
- **Deduplication** — Removes near-duplicate quotes (85% similarity)
- **AI Enhancement** — Optional Claude integration for better extraction

---

## Usage

### Basic Commands

```bash
# Scrape 50 books and 50 scripts (default)
python main.py

# Scrape only from Project Gutenberg
python main.py --source gutenberg

# Scrape only from movie scripts
python main.py --source scripts

# Scrape more sources
python main.py --max 100
```

### Output Options

```bash
# Save to new_quotes.json for review (default)
python main.py

# Merge directly into quotes.js
python main.py --merge

# Dry run - preview what would be added
python main.py --dry-run

# Save to custom file
python main.py --output my_quotes.json
```

### Cache Management

The scraper tracks what has been processed to avoid re-scraping the same sources.

```bash
# View cache statistics
python main.py --stats

# Force re-scrape (ignore cache)
python main.py --rescrape

# Clear the cache completely
python main.py --clear-cache
```

### All Options

| Flag | Description | Default |
|------|-------------|---------|
| `--source` | Source to scrape: `gutenberg`, `scripts`, or `all` | `all` |
| `--max` | Maximum items per source | `50` |
| `--merge` | Merge results into quotes.js | off |
| `--dry-run` | Preview merge without saving | off |
| `--output` | Custom output JSON file | — |
| `--rescrape` | Ignore processed cache | off |
| `--stats` | Show cache statistics | — |
| `--clear-cache` | Reset processed cache | — |

---

## Sources

### Project Gutenberg

- **70,000+ public domain books** available
- Fetches from [Gutendex API](https://gutendex.com) sorted by popularity
- Automatically extracts title and author from metadata
- Books are cached locally after download

### Movie Scripts (IMSDb)

- **1,200+ movie scripts** available
- Fetches list from [IMSDb](https://imsdb.com) alphabetical index
- Great for contemporary dialogue and time references

---

## How It Works

### 1. Time Pattern Detection

Regex patterns find various time formats:

| Pattern Type | Examples |
|--------------|----------|
| Digital | `3:45`, `3:45 PM`, `15:30` |
| O'clock | `seven o'clock`, `7 o'clock` |
| Named | `midnight`, `noon`, `midday` |
| Relative | `half past three`, `quarter to nine` |
| Minutes | `twenty minutes past four` |
| Contextual | `at five in the afternoon` |

### 2. Context Extraction

Captures ~150 characters before and after the time reference, trimmed to sentence boundaries when possible.

### 3. Quote Format

Outputs in the format expected by the clock:

```json
{
  "quote_first": "The clock struck ",
  "quote_time_case": "midnight",
  "quote_last": " and all was silent.",
  "title": "The Mystery Novel",
  "author": "Jane Author",
  "sfw": "yes"
}
```

### 4. Deduplication

- Removes quotes with 85%+ text similarity
- Prevents duplicates within time slots
- Checks against existing quotes.js when merging

### 5. Merging

Combines new quotes with existing `quotes.js`, preserving all current quotes while adding new ones.

---

## AI Enhancement (Optional)

For better quote extraction, you can enable Claude integration:

1. Create a `.env` file:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

2. The AI extractor can:
   - Refine quote boundaries for better readability
   - Determine AM/PM from context
   - Filter low-quality extractions

---

## Adding Custom Sources

Create a new source in `sources/`:

```python
from .base import BaseSource, SourceDocument

class MySource(BaseSource):
    @property
    def name(self) -> str:
        return "MySource"

    def get_documents(self):
        yield SourceDocument(
            text="Full text content...",
            title="Document Title",
            author="Author Name",
            source_id="mysource:123"  # For cache tracking
        )
```

Then register it in `sources/__init__.py` and add to `main.py`.

---

## File Structure

```
quote-scraper/
├── main.py              # CLI entry point
├── config.py            # Configuration settings
├── time_patterns.py     # Time detection regex
├── formatter.py         # Quote formatting
├── merger.py            # Merge with quotes.js
├── deduper.py           # Duplicate detection
├── processed_cache.py   # Track processed sources
├── ai_extractor.py      # Optional Claude integration
├── requirements.txt     # Python dependencies
├── sources/
│   ├── __init__.py
│   ├── base.py          # Base source class
│   ├── gutenberg.py     # Project Gutenberg source
│   └── scripts.py       # IMSDb movie scripts source
└── .gitignore
```

---

## Example Workflow

**Monthly update:**

```bash
# Activate environment
cd scripts/quote-scraper
source venv/bin/activate

# Check what's already been processed
python main.py --stats

# Scrape new sources (skips already processed)
python main.py --source all --max 100

# Review the results
cat new_quotes.json | head -100

# If happy, merge into quotes.js
python main.py --source all --max 100 --merge
```

**Full re-scrape:**

```bash
python main.py --clear-cache
python main.py --source all --max 200 --merge
```
