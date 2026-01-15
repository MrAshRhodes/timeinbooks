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

    def __init__(self, script_names: Optional[List[str]] = None, max_scripts: int = 50):
        self.script_names = script_names
        self.max_items = max_scripts  # Used by base class scrape loop
        self._available_scripts: List[str] = []

    @property
    def name(self) -> str:
        return "Scripts"

    def _fetch_all_scripts(self) -> List[str]:
        """Fetch list of all available scripts from IMSDb."""
        if self._available_scripts:
            return self._available_scripts

        print("  Fetching script list from IMSDb...")

        try:
            # IMSDb has an alphabetical listing
            url = f"{self.IMSDB_BASE}/all-scripts.html"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all script links
            scripts = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/Movie Scripts/' in href and href.endswith(' Script.html'):
                    # Extract script name from URL
                    name = href.replace('/Movie Scripts/', '').replace(' Script.html', '')
                    name = name.replace(' ', '-')
                    if name and name not in scripts:
                        scripts.append(name)

            print(f"  Found {len(scripts)} scripts available")
            self._available_scripts = scripts
            return scripts

        except Exception as e:
            print(f"  Warning: Could not fetch script list: {e}")
            return []

    def _fetch_scripts_paginated(self) -> Generator[str, None, None]:
        """Generator that yields script names one at a time."""
        all_scripts = self._fetch_all_scripts()
        for script_name in all_scripts:
            yield script_name

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

        except requests.RequestException:
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
        """Yield movie scripts. Iterates through all available scripts."""
        # Use provided script_names if given, otherwise fetch from IMSDb
        if self.script_names:
            script_source = iter(self.script_names)
        else:
            script_source = self._fetch_scripts_paginated()

        for script_name in script_source:
            text = self._get_script_text(script_name)
            if not text:
                continue

            text = self._clean_script_text(text)
            title = self._clean_script_name(script_name)

            yield SourceDocument(
                text=text,
                title=title,
                author="",
                source_id=f"imsdb:{script_name}"
            )
