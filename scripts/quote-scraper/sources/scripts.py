"""Movie and TV script quote source."""
import json
import os
import re
from typing import Generator, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, '..')
from config import (
    REQUEST_DELAY_SECONDS, MAX_WORKERS,
    MAX_RETRIES, RETRY_BACKOFF_FACTOR,
)
from .base import BaseSource, SourceDocument

# Disk cache directory for IMSDb data
IMSDB_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".imsdb_cache")
IMSDB_LIST_CACHE = os.path.join(IMSDB_CACHE_DIR, "_script_list.json")


def _create_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class ScriptSource(BaseSource):
    """Scrape quotes from movie scripts (IMSDb)."""

    IMSDB_BASE = "https://imsdb.com"

    def __init__(self, script_names: Optional[List[str]] = None, max_scripts: int = 50):
        self.script_names = script_names
        self.max_items = max_scripts  # Used by base class scrape loop
        self._available_scripts: List[str] = []
        self._session = _create_session()
        os.makedirs(IMSDB_CACHE_DIR, exist_ok=True)

    @property
    def name(self) -> str:
        return "Scripts"

    def _fetch_all_scripts(self) -> List[str]:
        """Fetch list of all available scripts from IMSDb (with disk cache)."""
        if self._available_scripts:
            return self._available_scripts

        # Check disk cache first
        if os.path.exists(IMSDB_LIST_CACHE):
            try:
                with open(IMSDB_LIST_CACHE, 'r') as f:
                    scripts = json.load(f)
                if scripts:
                    print(f"  Loaded {len(scripts)} scripts from cache")
                    self._available_scripts = scripts
                    return scripts
            except (json.JSONDecodeError, IOError):
                pass

        print("  Fetching script list from IMSDb...")

        try:
            # IMSDb has an alphabetical listing
            url = f"{self.IMSDB_BASE}/all-scripts.html"
            response = self._session.get(url, timeout=30)

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

            # Cache to disk
            with open(IMSDB_LIST_CACHE, 'w') as f:
                json.dump(scripts, f)

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
        """Download script from IMSDb (with disk cache)."""
        # Check disk cache first
        cache_path = os.path.join(IMSDB_CACHE_DIR, f"{script_name}.txt")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        url = f"{self.IMSDB_BASE}/scripts/{script_name}.html"

        try:
            response = self._session.get(url, timeout=30)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the script content (usually in <pre> tags)
            pre_tags = soup.find_all('pre')
            if pre_tags:
                text = pre_tags[0].get_text()
            else:
                # Alternative: look for scrtext class
                scrtext = soup.find(class_='scrtext')
                if scrtext:
                    text = scrtext.get_text()
                else:
                    return None

            # Cache to disk
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(text)

            return text

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

    def get_candidate_ids(self) -> Generator[Tuple[str, dict], None, None]:
        """Yield (source_id, metadata) for available IMSDb scripts."""
        if self.script_names:
            script_source = iter(self.script_names)
        else:
            script_source = self._fetch_scripts_paginated()

        for script_name in script_source:
            yield (f"imsdb:{script_name}", {"script_name": script_name})

    def fetch_document(self, source_id: str, metadata: dict) -> Optional[SourceDocument]:
        """Download a single script by name."""
        script_name = metadata["script_name"]
        text = self._get_script_text(script_name)
        if not text:
            return None

        text = self._clean_script_text(text)
        title = self._clean_script_name(script_name)

        return SourceDocument(
            text=text,
            title=title,
            author="",
            source_id=source_id
        )
