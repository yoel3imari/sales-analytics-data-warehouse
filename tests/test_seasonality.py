"""Unit tests for temporal seasonality multiplier logic."""

from datetime import date
from src.data.seasonality import DOW_MULTIPLIERS, MONTHLY_MULTIPLIERS, combined_multiplier


def test_month_multipliers():
    """Verify month seasonality multipliers fall within expected range."""
    for mult in MONTHLY_MULTIPLIERS:
        assert 0.5 <= mult <= 2.0


def test_dow_multipliers():
    """Verify day of week multipliers fall within expected range."""
    for mult in DOW_MULTIPLIERS:
        assert 0.5 <= mult <= 2.0


def test_combined_multiplier():
    """Verify combined seasonality multiplier returns positive float."""
    test_date = date(2025, 12, 25)
    mult = combined_multiplier(test_date)
    assert 0.3 <= mult <= 2.5
