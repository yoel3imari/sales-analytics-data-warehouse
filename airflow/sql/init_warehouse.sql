-- ============================================================
-- DuckDB Warehouse Initialization Script
--
-- Creates schemas (bronze, silver, gold, snapshots) and loads
-- raw CSV data into bronze tables via COPY INTO.
-- Idempotent: uses IF NOT EXISTS and CREATE OR REPLACE.
-- ============================================================

-- ── Schemas ──
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS snapshots;

-- ── Bronze: Raw Customers ──
CREATE OR REPLACE TABLE bronze.raw_customers AS
SELECT * FROM read_csv_auto('/data/raw/raw_customers.csv');

-- ── Bronze: Raw Products ──
CREATE OR REPLACE TABLE bronze.raw_products AS
SELECT * FROM read_csv_auto('/data/raw/raw_products.csv');

-- ── Bronze: Raw Sales ──
CREATE OR REPLACE TABLE bronze.raw_sales AS
SELECT * FROM read_csv_auto('/data/raw/raw_sales.csv');

-- ── Bronze: Raw Sales Stream ──
CREATE TABLE IF NOT EXISTS bronze.raw_sales_stream (
    event_id VARCHAR PRIMARY KEY,
    order_id VARCHAR,
    line_item_id BIGINT,
    order_date DATE,
    store_id VARCHAR,
    store_name VARCHAR,
    pos_terminal_id VARCHAR,
    customer_id VARCHAR,
    product_id VARCHAR,
    quantity BIGINT,
    unit_price DOUBLE,
    discount_amount DOUBLE,
    ship_date DATE,
    ship_city VARCHAR,
    ship_state VARCHAR,
    ship_country VARCHAR,
    channel VARCHAR,
    payment_method VARCHAR,
    created_at TIMESTAMP
);

-- ── Summary ──
SELECT 'bronze.raw_customers' as table_name, count(*) as row_count FROM bronze.raw_customers
UNION ALL
SELECT 'bronze.raw_products', count(*) FROM bronze.raw_products
UNION ALL
SELECT 'bronze.raw_sales', count(*) FROM bronze.raw_sales
UNION ALL
SELECT 'bronze.raw_sales_stream', count(*) FROM bronze.raw_sales_stream
ORDER BY table_name;

