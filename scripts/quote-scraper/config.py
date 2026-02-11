"""Configuration for quote scraper."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Scraping settings
CONTEXT_CHARS_BEFORE = 150  # Characters to capture before time reference
CONTEXT_CHARS_AFTER = 150   # Characters to capture after time reference
MIN_QUOTE_LENGTH = 50       # Minimum total quote length
MAX_QUOTE_LENGTH = 500      # Maximum total quote length

# Output paths
OUTPUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QUOTES_FILE = os.path.join(OUTPUT_DIR, "quotes.js")
NEW_QUOTES_FILE = os.path.join(OUTPUT_DIR, "scripts", "quote-scraper", "new_quotes.json")

# Gutenberg settings
GUTENBERG_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".gutenberg_cache")
POPULAR_BOOK_IDS = [
    1342,   # Pride and Prejudice
    84,     # Frankenstein
    1661,   # Sherlock Holmes
    11,     # Alice in Wonderland
    98,     # Tale of Two Cities
    2701,   # Moby Dick
    1952,   # The Yellow Wallpaper
    174,    # Picture of Dorian Gray
    345,    # Dracula
    16328,  # Beowulf
    100,    # Complete Works of Shakespeare
    1232,   # The Prince
    76,     # Adventures of Tom Sawyer
    74,     # Adventures of Huckleberry Finn
    1400,   # Great Expectations
]

# Network settings
REQUEST_DELAY_SECONDS = 0.5  # Delay between requests to be polite to servers
MAX_WORKERS = 5              # Number of parallel download threads
MAX_RETRIES = 3              # Number of retries for failed requests
RETRY_BACKOFF_FACTOR = 1.0   # Exponential backoff factor for retries
