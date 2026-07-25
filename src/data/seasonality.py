"""Seasonality multipliers for synthetic sales data generation.

Produces a combined multiplier in [0.3, 2.5] for any given date by composing:
- Monthly patterns (holiday lift in Nov/Dec, lull in Jan/Feb)
- Day-of-week patterns (higher mid-week, lower weekends)
- Holiday spikes (Christmas, Black Friday, New Year, Valentine's, Cyber Monday)
"""

from datetime import date, timedelta

import numpy as np

# Monthly multipliers: [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
MONTHLY_MULTIPLIERS = [0.7, 0.8, 0.9, 1.0, 1.0, 1.0, 1.1, 1.0, 1.1, 1.2, 1.5, 1.8]

# Day-of-week multipliers: [Mon, Tue, Wed, Thu, Fri, Sat, Sun]
DOW_MULTIPLIERS = [0.8, 1.0, 1.1, 1.1, 1.2, 1.0, 0.7]


def _get_black_friday(year: int) -> date:
    """Return the date of Black Friday (4th Friday of November) for the given year."""
    nov = date(year, 11, 1)
    # 4 = Friday in Python's weekday() (Mon=0, Sun=6)
    days_until_friday = (4 - nov.weekday()) % 7
    first_friday = nov + timedelta(days=days_until_friday)
    return first_friday + timedelta(days=21)  # 4th Friday = 1st + 21 days


def _get_cyber_monday(year: int) -> date:
    """Return the date of Cyber Monday (Monday after Black Friday)."""
    return _get_black_friday(year) + timedelta(days=3)


def combined_multiplier(dt: date, rng: np.random.Generator | None = None) -> float:
    """Compute a combined seasonality multiplier for a given date.

    The multiplier combines monthly patterns, day-of-week effects, and
    holiday spikes into a single factor in [0.3, 2.5].

    Args:
        dt: The date to compute the multiplier for.
        rng: Unused; kept for API consistency with other generator functions.

    Returns:
        A float multiplier between 0.3 and 2.5.
    """
    month_mult = MONTHLY_MULTIPLIERS[dt.month - 1]
    dow_mult = DOW_MULTIPLIERS[dt.weekday()]

    base = month_mult * dow_mult

    # Holiday spikes are additive on top of the base multiplier
    spike = 0.0

    # New Year (Jan 1)
    if dt.month == 1 and dt.day == 1:
        spike += 0.3

    # Valentine's Day (Feb 14)
    if dt.month == 2 and dt.day == 14:
        spike += 0.2

    # Black Friday (4th Friday of November)
    bf = _get_black_friday(dt.year)
    if dt == bf:
        spike += 0.8

    # Cyber Monday (Monday after Black Friday)
    cm = _get_cyber_monday(dt.year)
    if dt == cm:
        spike += 0.4

    # Christmas (Dec 25)
    if dt.month == 12 and dt.day == 25:
        spike += 0.5

    return min(2.5, base + spike)
