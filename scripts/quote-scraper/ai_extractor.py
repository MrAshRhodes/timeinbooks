"""AI-assisted quote extraction and refinement using Claude."""
import json
from typing import List, Optional, Dict

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY
from formatter import Quote


class AIExtractor:
    """Use Claude to refine and validate quote extractions."""

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def refine_quote(self, quote: Quote, full_context: str = "") -> Optional[Quote]:
        """Refine a quote's boundaries using AI."""
        prompt = f"""Given this extracted quote from a literary work, improve it by:
1. Adjusting boundaries to make it a complete, meaningful sentence or passage
2. Ensuring the time reference is naturally included
3. Keeping it concise but impactful

Current extraction:
- Before time: "{quote.quote_first}"
- Time text: "{quote.quote_time_case}"
- After time: "{quote.quote_last}"
- Source: {quote.title} by {quote.author}

{f'Additional context: {full_context[:500]}' if full_context else ''}

Return a JSON object with these exact fields:
{{
  "quote_first": "text before the time",
  "quote_time_case": "the time as it appears",
  "quote_last": "text after the time",
  "is_good_quote": true/false,
  "reason": "why this is or isn't a good quote"
}}

Only return the JSON, nothing else."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)

            if not result.get("is_good_quote", False):
                return None

            return Quote(
                quote_first=result["quote_first"],
                quote_time_case=result["quote_time_case"],
                quote_last=result["quote_last"],
                title=quote.title,
                author=quote.author,
                sfw="yes"
            )

        except Exception as e:
            print(f"  AI refinement failed: {e}")
            return quote  # Return original on failure

    def extract_from_text(self, text: str, title: str, author: str) -> List[Quote]:
        """Use AI to find and extract time-related quotes from text."""
        # Process in chunks to avoid token limits
        chunk_size = 4000
        quotes = []

        for i in range(0, min(len(text), 20000), chunk_size):
            chunk = text[i:i + chunk_size]
            chunk_quotes = self._extract_chunk(chunk, title, author)
            quotes.extend(chunk_quotes)

        return quotes

    def _extract_chunk(self, text: str, title: str, author: str) -> List[Quote]:
        """Extract quotes from a text chunk."""
        prompt = f"""Find all quotes in this text that mention specific times.
For each quote found, extract:
- The time in 24-hour format (HH:MM)
- The text before the time mention
- The exact time text as written
- The text after the time mention

Text from "{title}" by {author}:
---
{text}
---

Return a JSON array of objects:
[
  {{
    "time_24h": "HH:MM",
    "quote_first": "text before time",
    "quote_time_case": "time as written",
    "quote_last": "text after time"
  }}
]

Only return the JSON array, nothing else. If no time references found, return []."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            results = json.loads(response.content[0].text)

            return [
                Quote(
                    quote_first=r["quote_first"],
                    quote_time_case=r["quote_time_case"],
                    quote_last=r["quote_last"],
                    title=title,
                    author=author,
                    sfw="yes"
                )
                for r in results
            ]

        except Exception as e:
            print(f"  AI extraction failed: {e}")
            return []

    def determine_am_pm(self, quote: Quote, hour: int) -> str:
        """Use AI to determine if a time is AM or PM based on context."""
        if hour == 0 or hour == 12:
            return f"{hour:02d}"  # Midnight/noon are unambiguous

        prompt = f"""Based on this quote, is the time {hour}:00 AM or PM?

Quote: "{quote.quote_first}{quote.quote_time_case}{quote.quote_last}"
Source: {quote.title}

Consider context clues like:
- Time of day words (morning, evening, night)
- Activities mentioned (breakfast, dinner, sleeping)
- Scene descriptions

Reply with just "AM" or "PM" or "UNKNOWN" if truly ambiguous."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text.strip().upper()

            if result == "PM" and hour < 12:
                return f"{hour + 12:02d}"
            elif result == "AM":
                return f"{hour:02d}"
            else:
                return f"{hour:02d}"  # Default to AM for ambiguous

        except Exception:
            return f"{hour:02d}"
