"""Tests for time_patterns.py - all 6 pattern types."""
import sys
import os
import pytest

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from time_patterns import TimePatternMatcher, find_times, TimeMatch


@pytest.fixture
def matcher():
    return TimePatternMatcher()


# --- Digital pattern tests ---

class TestDigitalPattern:
    def test_basic_digital_time(self, matcher):
        matches = matcher.find_times("The clock showed 3:45 in the room.")
        assert len(matches) == 1
        assert "3:45" in matches[0].time_text
        assert matches[0].time_24h == "03:45"

    def test_digital_with_am(self, matcher):
        # Use phrasing that avoids "at N" to prevent AT_TIME_PATTERN overlap
        matches = matcher.find_times("She woke up, 7:30 am, to start her day.")
        assert len(matches) == 1
        assert matches[0].time_24h == "07:30"

    def test_digital_with_pm(self, matcher):
        # Use phrasing that avoids "at N" to prevent AT_TIME_PATTERN overlap
        matches = matcher.find_times("The meeting begins 2:15 PM sharp.")
        assert len(matches) == 1
        assert matches[0].time_24h == "14:15"

    def test_digital_24h_format(self, matcher):
        matches = matcher.find_times("The train departs at 15:30 today.")
        assert len(matches) == 1
        assert matches[0].time_24h == "15:30"

    def test_digital_with_dotted_ampm(self, matcher):
        matches = matcher.find_times("Arrival at 6:00 a.m. expected.")
        assert len(matches) == 1
        assert matches[0].time_24h == "06:00"

    def test_digital_invalid_hour_rejected(self, matcher):
        matches = matcher.find_times("The value was 25:99 which is invalid.")
        assert len(matches) == 0

    def test_digital_midnight(self, matcher):
        matches = matcher.find_times("It was exactly 0:00 when it happened.")
        assert len(matches) == 1
        assert matches[0].time_24h == "00:00"

    def test_digital_pm_context(self, matcher):
        matches = matcher.find_times("That evening around 8:30 they had dinner.")
        assert len(matches) == 1
        assert matches[0].time_24h == "20:30"


# --- O'clock pattern tests ---

class TestOclockPattern:
    def test_word_oclock(self, matcher):
        matches = matcher.find_times("It was seven o'clock in the morning.")
        assert len(matches) == 1
        assert matches[0].time_text == "seven o'clock"
        assert matches[0].time_24h == "07:00"

    def test_digit_oclock(self, matcher):
        matches = matcher.find_times("At 5 o'clock the bell rang.")
        assert len(matches) == 1
        assert matches[0].time_24h == "05:00"

    def test_twelve_oclock(self, matcher):
        matches = matcher.find_times("Twelve o'clock and all is well.")
        assert len(matches) == 1
        assert matches[0].time_24h == "12:00"

    def test_oclock_pm_context(self, matcher):
        matches = matcher.find_times("At nine o'clock that evening she retired.")
        assert len(matches) == 1
        assert matches[0].time_24h == "21:00"


# --- Named time pattern tests ---

class TestNamedPattern:
    def test_midnight(self, matcher):
        matches = matcher.find_times("The clock struck midnight and the spell broke.")
        assert len(matches) == 1
        assert matches[0].time_24h == "00:00"
        assert matches[0].time_text.lower() == "midnight"

    def test_noon(self, matcher):
        matches = matcher.find_times("We arrived at noon under the blazing sun.")
        assert len(matches) == 1
        assert matches[0].time_24h == "12:00"

    def test_midday(self, matcher):
        matches = matcher.find_times("By midday the heat was unbearable.")
        assert len(matches) == 1
        assert matches[0].time_24h == "12:00"


# --- Relative pattern tests (quarter/half past/to) ---

class TestRelativePattern:
    def test_quarter_past(self, matcher):
        matches = matcher.find_times("It was quarter past seven when he arrived.")
        assert len(matches) == 1
        assert matches[0].time_24h == "07:15"

    def test_half_past(self, matcher):
        matches = matcher.find_times("At half past three the ceremony began.")
        assert len(matches) == 1
        assert matches[0].time_24h == "03:30"

    def test_quarter_to(self, matcher):
        matches = matcher.find_times("It was quarter to nine and she hurried.")
        assert len(matches) == 1
        assert matches[0].time_24h == "08:45"

    def test_half_past_with_pm_context(self, matcher):
        matches = matcher.find_times("At half past six that evening they dined.")
        assert len(matches) == 1
        assert matches[0].time_24h == "18:30"

    def test_quarter_after(self, matcher):
        matches = matcher.find_times("A quarter after two the rain started.")
        assert len(matches) == 1
        assert matches[0].time_24h == "02:15"

    def test_quarter_before(self, matcher):
        matches = matcher.find_times("A quarter before five they departed.")
        assert len(matches) == 1
        assert matches[0].time_24h == "04:45"


# --- Minutes pattern tests ---

class TestMinutesPattern:
    def test_minutes_past(self, matcher):
        matches = matcher.find_times("At twenty minutes past four the train arrived.")
        assert len(matches) == 1
        assert matches[0].time_24h == "04:20"

    def test_ten_to(self, matcher):
        matches = matcher.find_times("It was ten to six and growing dark.")
        assert len(matches) == 1
        assert matches[0].time_24h == "05:50"

    def test_five_past(self, matcher):
        matches = matcher.find_times("Five past eleven the phone rang.")
        assert len(matches) == 1
        assert matches[0].time_24h == "11:05"

    def test_compound_minutes(self, matcher):
        matches = matcher.find_times("It was twenty-five past three in the afternoon.")
        assert len(matches) == 1
        assert matches[0].time_24h == "15:25"

    def test_minutes_before(self, matcher):
        matches = matcher.find_times("Fifteen minutes before eight the alarm sounded.")
        assert len(matches) == 1
        assert matches[0].time_24h == "07:45"


# --- At-time pattern tests ---

class TestAtTimePattern:
    def test_at_word_time(self, matcher):
        matches = matcher.find_times("She always arrived at five in the morning.")
        assert len(matches) == 1
        assert matches[0].time_24h == "05:00"

    def test_at_time_afternoon(self, matcher):
        matches = matcher.find_times("Meet me at three in the afternoon.")
        assert len(matches) == 1
        assert matches[0].time_24h == "15:00"

    def test_at_time_evening(self, matcher):
        matches = matcher.find_times("Dinner is at eight in the evening.")
        assert len(matches) == 1
        assert matches[0].time_24h == "20:00"

    def test_at_digit_time(self, matcher):
        matches = matcher.find_times("We leave at 6 in the morning.")
        assert len(matches) == 1
        assert matches[0].time_24h == "06:00"

    def test_at_time_no_context(self, matcher):
        matches = matcher.find_times("He said to arrive at seven for the party.")
        assert len(matches) >= 1
        # Without explicit AM/PM, uses context detection
        found = [m for m in matches if "seven" in m.time_text]
        assert len(found) == 1


# --- Multiple matches and edge cases ---

class TestEdgeCases:
    def test_multiple_times_in_text(self, matcher):
        text = "From 9:00 AM to 5:00 PM she worked tirelessly."
        matches = matcher.find_times(text)
        assert len(matches) == 2
        times = {m.time_24h for m in matches}
        assert "09:00" in times
        assert "17:00" in times

    def test_no_time_found(self, matcher):
        matches = matcher.find_times("The cat sat on the mat.")
        assert len(matches) == 0

    def test_empty_string(self, matcher):
        matches = matcher.find_times("")
        assert len(matches) == 0

    def test_module_level_find_times(self):
        """Test the convenience function."""
        matches = find_times("It was noon on a summer day.")
        assert len(matches) == 1
        assert matches[0].time_24h == "12:00"

    def test_matches_sorted_by_position(self, matcher):
        text = "At noon she left, arriving by 3:45 PM."
        matches = matcher.find_times(text)
        assert len(matches) == 2
        assert matches[0].start_pos < matches[1].start_pos
