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

# Kafka Streaming Configuration
KAFKA_BOOTSTRAP_SERVERS = ["localhost:19092", "localhost:9092", "redpanda:9092"]
KAFKA_SALES_TOPIC = "sales_events"

POS_STORES = [
    {
        "store_id": "STORE-101",
        "store_name": "NYC Flagship POS",
        "ship_city": "New York",
        "ship_state": "NY",
        "ship_country": "USA",
        "channel": "POS_Retail",
        "terminals": ["POS-101-A", "POS-101-B", "POS-101-C"],
    },
    {
        "store_id": "STORE-102",
        "store_name": "LA Downtown POS",
        "ship_city": "Los Angeles",
        "ship_state": "CA",
        "ship_country": "USA",
        "channel": "POS_Retail",
        "terminals": ["POS-102-A", "POS-102-B"],
    },
    {
        "store_id": "STORE-103",
        "store_name": "Chicago Loop POS",
        "ship_city": "Chicago",
        "ship_state": "IL",
        "ship_country": "USA",
        "channel": "POS_Retail",
        "terminals": ["POS-103-A", "POS-103-B"],
    },
    {
        "store_id": "STORE-104",
        "store_name": "London Store POS",
        "ship_city": "London",
        "ship_state": "ENG",
        "ship_country": "GBR",
        "channel": "POS_Retail",
        "terminals": ["POS-104-A"],
    },
    {
        "store_id": "STORE-105",
        "store_name": "E-Commerce Express POS",
        "ship_city": "Austin",
        "ship_state": "TX",
        "ship_country": "USA",
        "channel": "Online_Realtime",
        "terminals": ["POS-WEB-01", "POS-WEB-02"],
    },
]

STREAMING_SALE_COLUMNS = [
    "event_id",
    "order_id",
    "line_item_id",
    "order_date",
    "store_id",
    "store_name",
    "pos_terminal_id",
    "customer_id",
    "product_id",
    "quantity",
    "unit_price",
    "discount_amount",
    "ship_date",
    "ship_city",
    "ship_state",
    "ship_country",
    "channel",
    "payment_method",
    "created_at",
]

