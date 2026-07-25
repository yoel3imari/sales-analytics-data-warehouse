"""Synthetic data generator CLI for Sales Analytics Data Warehouse.

Generates customers, products, and sales CSV files under ``data/raw/``
with seeded reproducibility.

Usage:
    python -m src.generate --seed 42
    python -m src.generate --seed 42 --num-customers 5000 --num-products 60
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

import numpy as np
import pandas as pd

from src.config import (
    CUSTOMER_COLUMNS,
    NUM_CUSTOMERS,
    NUM_PRODUCTS,
    PRODUCT_COLUMNS,
    RANDOM_SEED,
    RAW_CUSTOMERS,
    RAW_DATA_DIR,
    RAW_PRODUCTS,
    RAW_SALES,
    SALE_COLUMNS,
)
from src.data.customers import generate_customers
from src.data.products import generate_products
from src.data.sales import generate_sales

logger = logging.getLogger("src.generate")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic sales data for the Sales Analytics Data Warehouse",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})",
    )
    parser.add_argument(
        "--num-customers",
        type=int,
        default=NUM_CUSTOMERS,
        help=f"Number of customers to generate (default: {NUM_CUSTOMERS})",
    )
    parser.add_argument(
        "--num-products",
        type=int,
        default=NUM_PRODUCTS,
        help=f"Number of products to generate (default: {NUM_PRODUCTS})",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2023-01-01",
        help="Simulation start date (default: 2023-01-01)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2025-12-31",
        help="Simulation end date (default: 2025-12-31)",
    )
    return parser.parse_args(argv)


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _write_csv(df: pd.DataFrame, path: str, label: str) -> None:
    """Write a DataFrame to CSV with summary logging."""
    rows = len(df)
    df.to_csv(path, index=False)
    logger.info("Wrote %s → %s (%d rows)", label, path, rows)


def main(argv: list[str] | None = None) -> int:
    """Execute the full data generation pipeline."""
    _setup_logging()
    args = parse_args(argv)

    seed = args.seed
    num_customers = args.num_customers
    num_products = args.num_products
    sim_start = date.fromisoformat(args.start_date)
    sim_end = date.fromisoformat(args.end_date)

    logger.info("=" * 60)
    logger.info("Sales Analytics Data Generator")
    logger.info("=" * 60)
    logger.info("Seed: %d", seed)
    logger.info("Customers: %d", num_customers)
    logger.info("Products: %d", num_products)
    logger.info("Date range: %s to %s", sim_start.isoformat(), sim_end.isoformat())

    # ── Seeded RNG ──
    rng = np.random.default_rng(seed)

    # ── Ensure output directory ──
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", RAW_DATA_DIR)

    # ── Products ──
    logger.info("Generating products …")
    products = generate_products(rng, num=num_products)
    df_products = pd.DataFrame(products, columns=PRODUCT_COLUMNS)
    _write_csv(df_products, RAW_PRODUCTS, "products")

    # ── Customers ──
    logger.info("Generating customers …")
    customers = generate_customers(rng, num=num_customers)
    df_customers = pd.DataFrame(customers, columns=CUSTOMER_COLUMNS)
    _write_csv(df_customers, RAW_CUSTOMERS, "customers")

    # ── Sales ──
    logger.info("Generating sales (day-by-day simulation) …")
    sales = generate_sales(
        customers,
        products,
        rng,
        start_date=sim_start,
        end_date=sim_end,
    )
    df_sales = pd.DataFrame(sales, columns=SALE_COLUMNS)
    _write_csv(df_sales, RAW_SALES, "sales")

    # ── Summary statistics ──
    actual_sales = len(df_sales) - 5  # exclude bad records from count
    logger.info("-" * 60)
    logger.info("SUMMARY")
    logger.info("  Products: %d", len(df_products))
    logger.info("  Customers: %d", len(df_customers))
    logger.info("  Sales rows (clean): %d", actual_sales)
    logger.info("  Bad records injected: 5")
    logger.info("  Sales rows (total): %d", len(df_sales))

    num_orders = df_sales["order_id"].nunique()
    logger.info("  Unique orders: %d", num_orders)

    if bool(df_sales["order_date"].notna().any()):
        sales_dates = df_sales["order_date"].dropna()
        logger.info("  Date range: %s to %s", sales_dates.min(), sales_dates.max())

    logger.info("=" * 60)
    logger.info("Generation complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
