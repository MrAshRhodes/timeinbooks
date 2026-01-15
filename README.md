# Quote O'Clock

A literary clock that tells time through quotes from books and movies. Each minute displays a quote that mentions that specific time, with a gentle page-turn animation between transitions.

## Features

- **Literary Quotes**: Displays quotes from books and movies that mention the current time, with the time portion highlighted in bold
- **Page Turn Animation**: Elegant book-like page turn effect when quotes change each minute (can be disabled in settings)
- **Light/Dark Mode**: Toggle between themes, or automatically follow system preference
- **12/24 Hour Format**: Switch between time formats - affects both the digital display and quote filtering (prefers quotes matching your format)
- **Timezone Selection**: Choose any timezone with auto-detection of your local zone
- **Fallback Display**: Shows the digital time when no quote is available for the current minute

## Usage

Simply open `index.html` in a browser. No build tools or server required.

### Settings

Click the gear icon to access:
- Page animation toggle
- 12/24 hour format toggle
- Timezone selector

Click the sun/moon icon to toggle dark mode.

## Project Structure

```
quote-o-clock/
├── index.html          # Main HTML structure
├── styles.css          # Styling with CSS variables for theming
├── app.js              # Application logic
├── quotes.js           # Quote database keyed by time (HH:MM)
├── README.md           # This file
└── scripts/
    └── quote-scraper/  # Utility to find new quotes (see below)
```

## Quote Scraper

A Python utility to find and extract new quotes containing time references from literature and movie scripts. Run monthly to expand the quote database.

### Quick Start

```bash
cd scripts/quote-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run a test scrape
python main.py --source gutenberg --max 5
```

### Features

- **Project Gutenberg**: Scrapes 70,000+ public domain books via Gutendex API
- **Movie Scripts**: Scrapes 1,200+ scripts from IMSDb
- **Smart Caching**: Tracks processed sources to avoid re-scraping
- **Time Pattern Detection**: Finds various time formats (digital, o'clock, named times, relative)
- **Deduplication**: Removes near-duplicate quotes (85% similarity)
- **AI Enhancement**: Optional Claude integration for better extraction

### Basic Commands

```bash
# Scrape 50 books and 50 scripts (default)
python main.py

# Scrape only from one source
python main.py --source gutenberg
python main.py --source scripts

# Scrape more sources
python main.py --max 100

# Merge results into quotes.js
python main.py --merge

# View what's been processed
python main.py --stats

# Force re-scrape (ignore cache)
python main.py --rescrape
```

See `scripts/quote-scraper/README.md` for full documentation.

## Credits

Initial quotes sourced from [literature-clock](https://github.com/JohannesNE/literature-clock) by Johannes Enevoldsen.

## License

MIT
