"""Time pattern detection and parsing."""
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class TimeMatch:
    """Represents a matched time reference in text."""
    time_24h: str           # "HH:MM" format
    time_text: str          # Original text (e.g., "half past seven")
    start_pos: int          # Start position in text
    end_pos: int            # End position in text
    am_pm_hint: Optional[str] = None  # "am", "pm", or None if ambiguous


# Number words to digits
WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50,
}

# Time of day hints for AM/PM
AM_HINTS = ["morning", "breakfast", "dawn", "sunrise", "a.m.", "am"]
PM_HINTS = ["afternoon", "evening", "night", "dinner", "dusk", "sunset", "p.m.", "pm", "midnight"]


def _word_to_hour(word: str) -> Optional[int]:
    """Convert word to hour number."""
    word = word.lower().strip()
    return WORD_TO_NUM.get(word)


def _parse_compound_minutes(text: str) -> Optional[int]:
    """Parse compound minute words like 'twenty-five'."""
    text = text.lower().strip()
    if "-" in text:
        parts = text.split("-")
        if len(parts) == 2:
            tens = WORD_TO_NUM.get(parts[0], 0)
            ones = WORD_TO_NUM.get(parts[1], 0)
            return tens + ones
    return WORD_TO_NUM.get(text)


def _detect_am_pm_context(text: str, match_pos: int, window: int = 100) -> Optional[str]:
    """Look for AM/PM hints in surrounding context."""
    start = max(0, match_pos - window)
    end = min(len(text), match_pos + window)
    context = text[start:end].lower()

    for hint in AM_HINTS:
        if hint in context:
            return "am"
    for hint in PM_HINTS:
        if hint in context:
            return "pm"
    return None


def _format_time_24h(hour: int, minute: int, am_pm: Optional[str] = None) -> str:
    """Format as HH:MM in 24-hour format."""
    # Handle AM/PM conversion
    if am_pm == "pm" and hour < 12:
        hour += 12
    elif am_pm == "am" and hour == 12:
        hour = 0

    return f"{hour:02d}:{minute:02d}"


class TimePatternMatcher:
    """Finds time references in text."""

    # Pattern: Digital time (e.g., "3:45", "3:45 PM", "15:30")
    DIGITAL_PATTERN = re.compile(
        r'\b(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?|AM|PM|am|pm)?\b',
        re.IGNORECASE
    )

    # Pattern: O'clock (e.g., "seven o'clock", "7 o'clock")
    OCLOCK_PATTERN = re.compile(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\s+o['\u2019]?clock\b",
        re.IGNORECASE
    )

    # Pattern: Named times
    NAMED_PATTERN = re.compile(
        r'\b(midnight|midday|noon)\b',
        re.IGNORECASE
    )

    # Pattern: Quarter/half past/to (e.g., "quarter past seven", "half past three")
    RELATIVE_PATTERN = re.compile(
        r'\b(quarter|half)\s+(past|to|after|before|of|till?)\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\b',
        re.IGNORECASE
    )

    # Pattern: Minutes past/to (e.g., "twenty minutes past four", "ten to six")
    MINUTES_PATTERN = re.compile(
        r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|twenty-one|twenty-two|twenty-three|twenty-four|twenty-five|twenty-six|twenty-seven|twenty-eight|twenty-nine|thirty|thirty-one|thirty-two|thirty-three|thirty-four|thirty-five|forty|forty-five|fifty|fifty-five|\d{1,2})\s+(minutes?\s+)?(past|to|after|before|of|till?)\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\b',
        re.IGNORECASE
    )

    # Pattern: "at [number] (in the morning/evening)"
    AT_TIME_PATTERN = re.compile(
        r'\bat\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})(\s+in\s+the\s+(morning|afternoon|evening|night))?\b',
        re.IGNORECASE
    )

    def find_times(self, text: str) -> List[TimeMatch]:
        """Find all time references in text."""
        matches = []

        # Digital times
        for m in self.DIGITAL_PATTERN.finditer(text):
            hour = int(m.group(1))
            minute = int(m.group(2))
            am_pm = m.group(3).lower().replace(".", "") if m.group(3) else None

            if hour > 23 or minute > 59:
                continue

            if am_pm is None and hour <= 12:
                am_pm = _detect_am_pm_context(text, m.start())

            matches.append(TimeMatch(
                time_24h=_format_time_24h(hour, minute, am_pm),
                time_text=m.group(0),
                start_pos=m.start(),
                end_pos=m.end(),
                am_pm_hint=am_pm
            ))

        # O'clock times
        for m in self.OCLOCK_PATTERN.finditer(text):
            hour_text = m.group(1)
            hour = _word_to_hour(hour_text) if not hour_text.isdigit() else int(hour_text)
            if hour is None or hour > 12:
                continue

            am_pm = _detect_am_pm_context(text, m.start())

            matches.append(TimeMatch(
                time_24h=_format_time_24h(hour, 0, am_pm),
                time_text=m.group(0),
                start_pos=m.start(),
                end_pos=m.end(),
                am_pm_hint=am_pm
            ))

        # Named times
        for m in self.NAMED_PATTERN.finditer(text):
            name = m.group(1).lower()
            if name == "midnight":
                time_24h = "00:00"
            else:  # noon, midday
                time_24h = "12:00"

            matches.append(TimeMatch(
                time_24h=time_24h,
                time_text=m.group(0),
                start_pos=m.start(),
                end_pos=m.end()
            ))

        # Relative times (quarter/half past/to)
        for m in self.RELATIVE_PATTERN.finditer(text):
            fraction = m.group(1).lower()
            direction = m.group(2).lower()
            hour_text = m.group(3)

            hour = _word_to_hour(hour_text) if not hour_text.isdigit() else int(hour_text)
            if hour is None or hour > 12:
                continue

            if fraction == "quarter":
                minutes = 15
            else:  # half
                minutes = 30

            if direction in ["past", "after"]:
                final_minute = minutes
                final_hour = hour
            else:  # to, before, of, till
                final_minute = 60 - minutes
                final_hour = hour - 1 if hour > 1 else 12

            am_pm = _detect_am_pm_context(text, m.start())

            matches.append(TimeMatch(
                time_24h=_format_time_24h(final_hour, final_minute, am_pm),
                time_text=m.group(0),
                start_pos=m.start(),
                end_pos=m.end(),
                am_pm_hint=am_pm
            ))

        # Minutes past/to
        for m in self.MINUTES_PATTERN.finditer(text):
            minutes_text = m.group(1)
            direction = m.group(3).lower()
            hour_text = m.group(4)

            minutes = _parse_compound_minutes(minutes_text)
            if minutes is None:
                minutes = int(minutes_text) if minutes_text.isdigit() else None
            if minutes is None or minutes > 59:
                continue

            hour = _word_to_hour(hour_text) if not hour_text.isdigit() else int(hour_text)
            if hour is None or hour > 12:
                continue

            if direction in ["past", "after"]:
                final_minute = minutes
                final_hour = hour
            else:  # to, before, of, till
                final_minute = 60 - minutes
                final_hour = hour - 1 if hour > 1 else 12

            am_pm = _detect_am_pm_context(text, m.start())

            matches.append(TimeMatch(
                time_24h=_format_time_24h(final_hour, final_minute, am_pm),
                time_text=m.group(0),
                start_pos=m.start(),
                end_pos=m.end(),
                am_pm_hint=am_pm
            ))

        # "at [time]" patterns
        for m in self.AT_TIME_PATTERN.finditer(text):
            hour_text = m.group(1)
            time_of_day = m.group(3)

            hour = _word_to_hour(hour_text) if not hour_text.isdigit() else int(hour_text)
            if hour is None or hour > 12:
                continue

            if time_of_day:
                am_pm = "am" if time_of_day.lower() == "morning" else "pm"
            else:
                am_pm = _detect_am_pm_context(text, m.start())

            matches.append(TimeMatch(
                time_24h=_format_time_24h(hour, 0, am_pm),
                time_text=m.group(0),
                start_pos=m.start(),
                end_pos=m.end(),
                am_pm_hint=am_pm
            ))

        # Sort by position and remove duplicates
        matches.sort(key=lambda x: x.start_pos)

        # Remove overlapping matches (keep first)
        filtered = []
        last_end = -1
        for match in matches:
            if match.start_pos >= last_end:
                filtered.append(match)
                last_end = match.end_pos

        return filtered


# Module-level instance for convenience
matcher = TimePatternMatcher()


def find_times(text: str) -> List[TimeMatch]:
    """Find all time references in text."""
    return matcher.find_times(text)
