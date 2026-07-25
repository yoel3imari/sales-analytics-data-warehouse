"""Customer generator for synthetic sales data.

Generates 10 000 customers with demographics, cohort assignment,
and realistic US address distribution.
"""

from datetime import date

import numpy as np
from faker import Faker

from src.data.cohorts import assign_cohort

# Income bracket → conditional probability weights per cohort
# Order: LOW, MEDIUM, HIGH, VERY_HIGH
_INCOME_PROFILES: dict[str, list[float]] = {
    "LOYAL_HEAVY": [0.10, 0.30, 0.40, 0.20],
    "LOYAL_LIGHT": [0.15, 0.40, 0.30, 0.15],
    "GROWING": [0.20, 0.40, 0.30, 0.10],
    "DECLINING": [0.35, 0.40, 0.20, 0.05],
    "ONE_SHOT": [0.40, 0.35, 0.20, 0.05],
    "CHURN_RISK": [0.50, 0.30, 0.15, 0.05],
}

_INCOME_BRACKETS = ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]


def generate_customers(
    rng: np.random.Generator,
    *,
    num: int = 10000,
) -> list[dict]:
    """Generate a list of customer records.

    Args:
        rng: Seeded NumPy random generator for reproducibility.
        num: Number of customers to generate.

    Returns:
        List of customer dicts matching the CUSTOMER_COLUMNS schema
        from src.config.
    """
    fake = Faker()
    Faker.seed(int(rng.integers(0, 2**31)))

    signup_start = date(2022, 1, 1)
    signup_end = date(2025, 12, 31)
    signup_ord_start = signup_start.toordinal()
    signup_ord_end = signup_end.toordinal()

    birth_start = date(1950, 1, 1)
    birth_end = date(2002, 12, 31)
    birth_ord_start = birth_start.toordinal()
    birth_ord_end = birth_end.toordinal()

    customers: list[dict] = []
    for i in range(1, num + 1):
        cohort = assign_cohort(rng)
        gender = rng.choice(["M", "F"])

        first_name = fake.first_name_male() if gender == "M" else fake.first_name_female()
        last_name = fake.last_name()

        email = f"{first_name.lower()}.{last_name.lower()}@example.com"

        signup_ord = int(rng.integers(signup_ord_start, signup_ord_end + 1))
        signup_date = date.fromordinal(signup_ord)

        birth_ord = int(rng.integers(birth_ord_start, birth_ord_end + 1))
        birth_date = date.fromordinal(birth_ord)

        # Income bracket correlated with cohort
        income_probs = _INCOME_PROFILES[cohort.name]
        income_idx = int(rng.choice(len(_INCOME_BRACKETS), p=income_probs))  # type: ignore[arg-type]
        income_bracket = _INCOME_BRACKETS[income_idx]

        # Address
        address_line1 = fake.street_address()
        address_line2 = fake.secondary_address() if rng.random() < 0.3 else ""
        city = fake.city()
        state = fake.state_abbr()
        postal_code = fake.zipcode()

        customers.append({
            "customer_id": f"CUST-{i:05d}",
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": fake.phone_number(),
            "address_line1": address_line1,
            "address_line2": address_line2,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": "USA",
            "birth_date": birth_date.isoformat(),
            "gender": gender,
            "income_bracket": income_bracket,
            "cohort": cohort.name,
            "signup_date": signup_date.isoformat(),
            "last_update_date": signup_date.isoformat(),
        })

    return customers
