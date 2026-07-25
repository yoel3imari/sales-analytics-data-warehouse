"""Customer behavior cohort definitions for synthetic data generation.

Six distinct cohorts model realistic customer purchasing patterns:
- LOYAL_HEAVY: Frequent buyers, low churn, high quantities
- LOYAL_LIGHT: Regular buyers, moderate churn
- GROWING: Increasing engagement, moderate churn
- DECLINING: Waning engagement, higher churn
- ONE_SHOT: Very infrequent, high churn (buy once per year at most)
- CHURN_RISK: Low engagement, very high churn
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Cohort:
    """Defines a customer behavior segment with purchase and churn characteristics.

    Attributes:
        name: Unique cohort identifier.
        weight: Proportion of customers assigned to this cohort (sums to 1.0).
        p_buy_on_day: Base probability a customer buys on any given day.
        p_churn_per_year: Probability of churning each calendar year.
        mean_qty: Mean quantity per purchase line item.
        std_qty: Standard deviation of quantity per line item.
        price_sensitivity: 0-1 scale; higher = more responsive to discounts.
        days_between_purchases: Average gap between purchases (informational).
    """

    name: str
    weight: float
    p_buy_on_day: float
    p_churn_per_year: float
    mean_qty: float
    std_qty: float
    price_sensitivity: float
    days_between_purchases: int


COHORTS = [
    Cohort(
        name="LOYAL_HEAVY",
        weight=0.15,
        p_buy_on_day=0.12,
        p_churn_per_year=0.05,
        mean_qty=3.0,
        std_qty=1.0,
        price_sensitivity=0.2,
        days_between_purchases=14,
    ),
    Cohort(
        name="LOYAL_LIGHT",
        weight=0.20,
        p_buy_on_day=0.06,
        p_churn_per_year=0.08,
        mean_qty=1.5,
        std_qty=0.5,
        price_sensitivity=0.3,
        days_between_purchases=30,
    ),
    Cohort(
        name="GROWING",
        weight=0.20,
        p_buy_on_day=0.04,
        p_churn_per_year=0.10,
        mean_qty=2.0,
        std_qty=0.8,
        price_sensitivity=0.4,
        days_between_purchases=45,
    ),
    Cohort(
        name="DECLINING",
        weight=0.15,
        p_buy_on_day=0.03,
        p_churn_per_year=0.25,
        mean_qty=1.5,
        std_qty=0.7,
        price_sensitivity=0.5,
        days_between_purchases=60,
    ),
    Cohort(
        name="ONE_SHOT",
        weight=0.15,
        p_buy_on_day=0.01,
        p_churn_per_year=0.50,
        mean_qty=1.2,
        std_qty=0.4,
        price_sensitivity=0.6,
        days_between_purchases=365,
    ),
    Cohort(
        name="CHURN_RISK",
        weight=0.15,
        p_buy_on_day=0.02,
        p_churn_per_year=0.40,
        mean_qty=1.0,
        std_qty=0.3,
        price_sensitivity=0.7,
        days_between_purchases=90,
    ),
]

_COHORT_BY_NAME: dict[str, Cohort] = {c.name: c for c in COHORTS}


def get_cohort_by_name(name: str) -> Cohort:
    """Look up a Cohort by its name string.

    Args:
        name: Cohort name (e.g. 'LOYAL_HEAVY').

    Returns:
        The matching Cohort dataclass.

    Raises:
        KeyError: If no cohort matches the given name.
    """
    return _COHORT_BY_NAME[name]


def assign_cohort(rng: np.random.Generator) -> Cohort:
    """Assign a customer to a cohort using weighted random selection.

    Args:
        rng: Seeded NumPy random generator for reproducibility.

    Returns:
        A Cohort dataclass selected according to the predefined weights.
    """
    weights = [c.weight for c in COHORTS]
    idx: int = rng.choice(len(COHORTS), p=weights)  # type: ignore[arg-type]
    return COHORTS[idx]
