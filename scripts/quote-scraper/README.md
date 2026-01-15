# Quote Scraper

A utility to find and extract quotes containing time references from various sources.

## Setup

```bash
cd scripts/quote-scraper
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

For AI-assisted extraction (optional), create a `.env` file:
```
ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

### Basic Scraping

```bash
# Scrape from all sources (default)
python main.py

# Scrape only from Project Gutenberg
python main.py --source gutenberg --max 10

# Scrape only from movie scripts
python main.py --source scripts --max 10
```

### Output Options

```bash
# Preview - save to new_quotes.json for review
python main.py --source gutenberg

# Merge into quotes.js
python main.py --source all --merge

# Dry run - check what would be added without modifying quotes.js
python main.py --source all --dry-run

# Save to custom file
python main.py --source gutenberg --output my_quotes.json
```

## Sources

### Project Gutenberg
- Public domain books (70,000+ available)
- Classic literature with known authors
- Pre-configured with popular titles

### Movie Scripts (IMSDb)
- Contemporary dialogue
- Pre-configured with popular movies

## How It Works

1. **Pattern Detection**: Regex patterns find time references:
   - Digital: "3:45", "3:45 PM"
   - Words: "seven o'clock", "half past three"
   - Named: "midnight", "noon"
   - Relative: "quarter to nine", "twenty minutes past four"

2. **Context Extraction**: Captures ~150 characters before/after the time

3. **Formatting**: Converts to the quote clock format:
   ```json
   {
     "quote_first": "text before time",
     "quote_time_case": "the time as written",
     "quote_last": "text after time",
     "title": "Source title",
     "author": "Author name",
     "sfw": "yes"
   }
   ```

4. **Deduplication**: Removes near-duplicate quotes (85% similarity threshold)

5. **Merging**: Combines with existing quotes.js

## Adding New Sources

Create a new source in `sources/`:

```python
from .base import BaseSource, SourceDocument

class MySource(BaseSource):
    @property
    def name(self) -> str:
        return "MySource"

    def get_documents(self):
        yield SourceDocument(
            text="...",
            title="...",
            author="..."
        )
```

## Files

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point |
| `time_patterns.py` | Time detection regex |
| `formatter.py` | Quote formatting |
| `merger.py` | Merge with quotes.js |
| `deduper.py` | Duplicate detection |
| `ai_extractor.py` | Optional Claude integration |
| `sources/` | Quote sources |
