"""Movie and TV script quote source."""
import re
from typing import Generator, List, Optional

import requests
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, '..')
from .base import BaseSource, SourceDocument


class ScriptSource(BaseSource):
    """Scrape quotes from movie scripts (IMSDb)."""

    IMSDB_BASE = "https://imsdb.com"

    # Popular movies likely to have time references
    POPULAR_SCRIPTS = [
        "Back-to-the-Future",
        "Groundhog-Day",
        "12-Angry-Men",
        "Casablanca",
        "The-Breakfast-Club",
        "Ferris-Buellers-Day-Off",
        "When-Harry-Met-Sally",
        "Before-Sunrise",
        "Lost-in-Translation",
        "Pulp-Fiction",
        "The-Godfather",
        "Goodfellas",
        "Reservoir-Dogs",
        "Die-Hard",
        "Alien",
        "The-Shining",
        "Jaws",
        "E-T-The-Extra-Terrestrial",
        "Forrest-Gump",
        "The-Matrix",
    ]

    def __init__(self, script_names: Optional[List[str]] = None, max_scripts: int = 20):
        self.script_names = script_names or self.POPULAR_SCRIPTS
        self.max_scripts = max_scripts

    @property
    def name(self) -> str:
        return "Scripts"

    def _get_script_text(self, script_name: str) -> Optional[str]:
        """Download script from IMSDb."""
        url = f"{self.IMSDB_BASE}/scripts/{script_name}.html"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the script content (usually in <pre> tags)
            pre_tags = soup.find_all('pre')
            if pre_tags:
                return pre_tags[0].get_text()

            # Alternative: look for scrtext class
            scrtext = soup.find(class_='scrtext')
            if scrtext:
                return scrtext.get_text()

            return None

        except requests.RequestException as e:
            print(f"  Warning: Could not download {script_name}: {e}")
            return None

    def _clean_script_name(self, name: str) -> str:
        """Convert URL-friendly name to display title."""
        return name.replace("-", " ").title()

    def _clean_script_text(self, text: str) -> str:
        """Clean up script formatting."""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove scene headings for cleaner quotes
        text = re.sub(r'^(INT\.|EXT\.|INT/EXT).*$', '', text, flags=re.MULTILINE)
        return text.strip()

    def get_documents(self) -> Generator[SourceDocument, None, None]:
        """Yield movie scripts."""
        for script_name in self.script_names[:self.max_scripts]:
            text = self._get_script_text(script_name)
            if not text:
                continue

            text = self._clean_script_text(text)
            title = self._clean_script_name(script_name)

            yield SourceDocument(
                text=text,
                title=title,
                author="",  # Scripts don't have a single author
                source_id=f"imsdb:{script_name}"
            )
