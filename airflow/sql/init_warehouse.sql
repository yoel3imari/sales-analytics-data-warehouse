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

-- ── Summary ──
SELECT 'bronze.raw_customers' as table_name, count(*) as row_count FROM bronze.raw_customers
UNION ALL
SELECT 'bronze.raw_products', count(*) FROM bronze.raw_products
UNION ALL
SELECT 'bronze.raw_sales', count(*) FROM bronze.raw_sales
ORDER BY table_name;
