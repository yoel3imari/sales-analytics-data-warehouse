"""Day-by-day sales simulation engine.

Generates synthetic sales transactions by simulating customer purchase
behaviour day-by-day over a configurable date range. Uses seeded RNG
for full reproducibility and injects 5 intentionally bad records for
data-quality testing downstream.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import date, timedelta

import numpy as np

from src.data.cohorts import get_cohort_by_name
from src.data.seasonality import combined_multiplier

logger = logging.getLogger(__name__)

# Average number of line items per purchase, by cohort
_COHORT_AVG_LINES: dict[str, float] = {
    "LOYAL_HEAVY": 3.0,
    "LOYAL_LIGHT": 2.0,
    "GROWING": 2.5,
    "DECLINING": 2.0,
    "ONE_SHOT": 1.2,
    "CHURN_RISK": 1.5,
}

# Channel distribution
_CHANNELS = ["Online", "Retail", "Catalog", "B2B"]
_CHANNEL_PROBS = [0.60, 0.25, 0.10, 0.05]


def _order_id_gen(prefix: str = "ORD-", start: int = 1) -> Iterator[str]:
    """Yield sequential order IDs formatted with zero-padding."""
    counter = start
    while True:
        yield f"{prefix}{counter:08d}"
        counter += 1


def _build_product_availability(
    products: list[dict],
    start_date: date,
    end_date: date,
) -> dict[date, list[dict]]:
    """Pre-compute lists of available products for each day.

    Filters products by their launch and (optional) discontinued dates.
    """
    available: dict[date, list[dict]] = {}
    current = start_date
    while current <= end_date:
        avail = [
            p
            for p in products
            if p["_launch_date"] <= current
            and (p["_discontinued_date"] is None or p["_discontinued_date"] > current)
        ]
        if avail:
            available[current] = avail
        current += timedelta(days=1)
    return available


def _inject_bad_data(sales: list[dict], rng: np.random.Generator) -> list[dict]:
    """Create 5 intentionally corrupted records for data-quality testing.

    Bad records injected:
    1. null_customer  – sale with ``customer_id`` set to ``None``.
    2. negative_qty   – sale with ``quantity`` = -3.
    3. future_date    – sale with ``order_date`` = 2099-01-01.
    4. duplicate_order – exact duplicate of an existing sale.
    5. zero_price     – sale with ``unit_price`` = 0.0.
    """
    if not sales:
        return []

    bad: list[dict] = []

    # 1. Null customer_id
    idx = int(rng.integers(0, len(sales)))
    rec = dict(sales[idx])
    rec["customer_id"] = None
    bad.append(rec)

    # 2. Negative quantity
    idx = int(rng.integers(0, len(sales)))
    rec = dict(sales[idx])
    rec["quantity"] = -3
    bad.append(rec)

    # 3. Future date
    idx = int(rng.integers(0, len(sales)))
    rec = dict(sales[idx])
    rec["order_date"] = "2099-01-01"
    bad.append(rec)

    # 4. Duplicate order – pick a single existing sale row and duplicate it
    idx = int(rng.integers(0, len(sales)))
    rec = dict(sales[idx])
    bad.append(rec)

    # 5. Zero price
    idx = int(rng.integers(0, len(sales)))
    rec = dict(sales[idx])
    rec["unit_price"] = 0.0
    rec["discount_amount"] = 0.0
    bad.append(rec)

    logger.info("Injected %d bad records into sales data", len(bad))
    return bad


def generate_sales(
    customers_data: list[dict],
    products_data: list[dict],
    rng: np.random.Generator,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Generate synthetic sales transactions day-by-day.

    For each day in the simulation range, the function iterates over
    every active (non-churned) customer and rolls for a purchase based
    on their cohort's daily probability and the seasonality multiplier.
    Each purchase generates 1--5 line items.

    Args:
        customers_data: List of customer dicts with ``signup_date``,
            ``cohort``, ``city``, ``state``, ``country``, ``customer_id``.
        products_data: List of product dicts with ``list_price``,
            ``launch_date``, ``discontinued_date``, ``product_id``.
        rng: Seeded NumPy generator for reproducibility.
        start_date: First day of simulation (default 2023-01-01).
        end_date: Last day of simulation (default 2025-12-31).

    Returns:
        List of sale line-item dicts matching ``SALE_COLUMNS`` schema
        from ``src.config``.
    """
    if start_date is None:
        start_date = date(2023, 1, 1)
    if end_date is None:
        end_date = date(2025, 12, 31)

    # ── Pre-process dates for fast comparison ──
    for c in customers_data:
        c["_signup"] = date.fromisoformat(c["signup_date"])  # noqa: PD011
    for p in products_data:
        p["_launch_date"] = date.fromisoformat(p["launch_date"])  # noqa: PD011
        p["_discontinued_date"] = (  # noqa: PD011
            date.fromisoformat(p["discontinued_date"])
            if p.get("discontinued_date")
            else None
        )

    # ── Pre-compute available products per day ──
    logger.info("Pre-computing product availability by day …")
    available_by_day = _build_product_availability(products_data, start_date, end_date)
    logger.info("Done — %d days with available products", len(available_by_day))

    # ── State ──
    sales: list[dict] = []
    churned: set[str] = set()
    oid_gen = _order_id_gen()
    current = start_date

    # Churn check: Jan 1 of each year *after* the first year
    churn_years = set(range(start_date.year + 1, end_date.year + 1))

    # For logging progress
    log_interval = timedelta(days=90)
    next_log = start_date + log_interval

    # ── Main simulation loop ──
    while current <= end_date:
        if current >= next_log:
            logger.info(
                "  %s — %d sales rows generated, %d customers churned",
                current.isoformat(),
                len(sales),
                len(churned),
            )
            next_log = current + log_interval

        mult = combined_multiplier(current)

        # ── Annual churn checkpoint (Jan 1) ──
        if current.month == 1 and current.day == 1 and current.year in churn_years:
            for c in customers_data:
                cid: str = c["customer_id"]
                if cid in churned:
                    continue
                if c["_signup"] < current:
                    cohort = get_cohort_by_name(c["cohort"])
                    if rng.random() < cohort.p_churn_per_year:
                        churned.add(cid)
            logger.info(
                "  Churn checkpoint %s — %d customers churned so far",
                current.isoformat(),
                len(churned),
            )

        # ── Available products for today ──
        today_products = available_by_day.get(current)
        if not today_products:
            current += timedelta(days=1)
            continue

        # ── Iterate active customers ──
        for c in customers_data:
            cid = c["customer_id"]
            if cid in churned:
                continue
            if current < c["_signup"]:
                continue

            cohort = get_cohort_by_name(c["cohort"])
            buy_prob = cohort.p_buy_on_day * mult

            if rng.random() >= buy_prob:
                continue

            # ── Purchase event ──
            order_id = next(oid_gen)

            # Number of line items (clamped 1–5)
            avg_lines = _COHORT_AVG_LINES[cohort.name]
            num_lines = max(1, min(5, int(round(rng.normal(avg_lines, 0.8)))))

            # Channel
            channel = _CHANNELS[int(rng.choice(len(_CHANNELS), p=_CHANNEL_PROBS))]  # type: ignore[arg-type]

            # Ship date (2–7 days after order, capped at end_date)
            ship_days = int(rng.integers(2, 8))
            ship_date = min(current + timedelta(days=ship_days), end_date)

            for li in range(num_lines):
                product = today_products[int(rng.integers(0, len(today_products)))]

                # Quantity (normal distribution around cohort mean)
                qty = max(1, int(round(rng.normal(cohort.mean_qty, cohort.std_qty))))

                # Price variation (-5% markup to +10% discount)
                variation = rng.uniform(-0.05, 0.10)
                if variation > 0:
                    effective_discount = variation * (1.0 + cohort.price_sensitivity * 0.5)
                else:
                    effective_discount = variation
                effective_discount = max(-0.15, min(0.25, effective_discount))

                list_price = float(product["list_price"])
                unit_price = round(list_price * (1.0 - effective_discount), 2)
                discount_amount = round(list_price * effective_discount, 2)

                sales.append({
                    "order_id": order_id,
                    "line_item_id": li + 1,
                    "order_date": current.isoformat(),
                    "customer_id": cid,
                    "product_id": product["product_id"],
                    "quantity": qty,
                    "unit_price": unit_price,
                    "discount_amount": discount_amount,
                    "ship_date": ship_date.isoformat(),
                    "ship_city": c["city"],
                    "ship_state": c["state"],
                    "ship_country": c["country"],
                    "channel": channel,
                })

        current += timedelta(days=1)

    logger.info(
        "Sales generation complete: %d rows across %d orders",
        len(sales),
        sum(1 for s in sales if s["line_item_id"] == 1),
    )

    # ── Inject bad data ──
    bad = _inject_bad_data(sales, rng)
    sales.extend(bad)

    return sales
