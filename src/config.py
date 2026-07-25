"""Shared configuration constants for the Sales Analytics project."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
WAREHOUSE_DIR = DATA_DIR / "warehouse"

# DuckDB
DUCKDB_PATH = str(WAREHOUSE_DIR / "sales_analytics.duckdb")

# Raw data files
RAW_CUSTOMERS = str(RAW_DATA_DIR / "raw_customers.csv")
RAW_PRODUCTS = str(RAW_DATA_DIR / "raw_products.csv")
RAW_SALES = str(RAW_DATA_DIR / "raw_sales.csv")

# Generation parameters
RANDOM_SEED = 42
NUM_CUSTOMERS = 10000
NUM_PRODUCTS = 80
MIN_SALES_ROWS = 100_000
MAX_SALES_ROWS = 500_000
YEARS_OF_HISTORY = 3

# Bad data injection (intentional)
NUM_BAD_RECORDS = 5

# Column definitions
CUSTOMER_COLUMNS = [
    "customer_id", "first_name", "last_name", "email", "phone",
    "address_line1", "address_line2", "city", "state", "postal_code",
    "country", "birth_date", "gender", "income_bracket", "cohort",
    "signup_date", "last_update_date",
]

PRODUCT_COLUMNS = [
    "product_id", "product_name", "category", "subcategory", "brand",
    "list_price", "standard_cost", "color", "size", "weight_kg",
    "launch_date", "discontinued_date",
]

SALE_COLUMNS = [
    "order_id", "line_item_id", "order_date", "customer_id", "product_id",
    "quantity", "unit_price", "discount_amount", "ship_date", "ship_city",
    "ship_state", "ship_country", "channel",
]

# Date range for dim_date
DATE_START = "2022-01-01"
DATE_END = "2026-12-31"
