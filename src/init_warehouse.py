"""Initialize the DuckDB warehouse: create schemas and load CSVs into bronze tables.

Usage:
    uv run python -m src.init_warehouse
"""

from __future__ import annotations

import logging
import sys

import duckdb

from src.config import (
    DUCKDB_PATH,
    RAW_CUSTOMERS,
    RAW_PRODUCTS,
    RAW_SALES,
)

logger = logging.getLogger("src.init_warehouse")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    _setup_logging()

    logger.info("=" * 60)
    logger.info("DuckDB Warehouse Initialization")
    logger.info("=" * 60)
    logger.info("Database: %s", DUCKDB_PATH)

    conn = duckdb.connect(DUCKDB_PATH)

    # ── Create schemas ──
    logger.info("Creating schemas …")
    conn.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    conn.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    conn.execute("CREATE SCHEMA IF NOT EXISTS gold;")
    conn.execute("CREATE SCHEMA IF NOT EXISTS snapshots;")

    # ── Load raw CSVs into bronze tables ──
    logger.info("Loading raw_customers.csv → bronze.raw_customers …")
    conn.execute(f"""
        CREATE OR REPLACE TABLE bronze.raw_customers AS
        SELECT * FROM read_csv_auto('{RAW_CUSTOMERS}');
    """)

    logger.info("Loading raw_products.csv → bronze.raw_products …")
    conn.execute(f"""
        CREATE OR REPLACE TABLE bronze.raw_products AS
        SELECT * FROM read_csv_auto('{RAW_PRODUCTS}');
    """)

    logger.info("Loading raw_sales.csv → bronze.raw_sales …")
    conn.execute(f"""
        CREATE OR REPLACE TABLE bronze.raw_sales AS
        SELECT * FROM read_csv_auto('{RAW_SALES}');
    """)

    # ── Summary ──
    results = conn.execute("""
        SELECT 'bronze.raw_customers' AS table_name, COUNT(*) AS row_count FROM bronze.raw_customers
        UNION ALL
        SELECT 'bronze.raw_products', COUNT(*) FROM bronze.raw_products
        UNION ALL
        SELECT 'bronze.raw_sales', COUNT(*) FROM bronze.raw_sales
        ORDER BY table_name
    """).fetchall()

    logger.info("-" * 60)
    logger.info("SUMMARY")
    for table, count in results:
        logger.info("  %s: %d rows", table, count)
    logger.info("=" * 60)
    logger.info("Warehouse initialization complete.")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
