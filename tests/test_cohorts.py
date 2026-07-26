"""Unit tests for customer cohort generation logic."""

import numpy as np
from src.data.cohorts import COHORTS, Cohort, assign_cohort, get_cohort_by_name


def test_cohort_definitions():
    """Verify cohort dictionary contains expected cohort types."""
    assert len(COHORTS) == 6
    cohort_names = [c.name for c in COHORTS]
    assert "LOYAL_HEAVY" in cohort_names
    assert "CHURN_RISK" in cohort_names
    for cohort in COHORTS:
        assert isinstance(cohort, Cohort)
        assert cohort.weight > 0
        assert 0.0 <= cohort.p_churn_per_year <= 1.0


def test_assign_cohort_distribution():
    """Verify cohort assignment returns valid Cohort objects."""
    rng = np.random.default_rng(42)
    cohort = assign_cohort(rng)
    assert isinstance(cohort, Cohort)
    assert cohort.name in [c.name for c in COHORTS]


def test_get_cohort_by_name():
    """Verify lookup of cohort by name string."""
    cohort = get_cohort_by_name("LOYAL_HEAVY")
    assert isinstance(cohort, Cohort)
    assert cohort.name == "LOYAL_HEAVY"
