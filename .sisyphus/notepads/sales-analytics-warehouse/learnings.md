
## Task 10: dbt Dimension Models & Snapshots (Completed)
- Created 3 dimension models (dim_customer, dim_product, dim_date) as tables in marts/
- Created 2 SCD Type 2 snapshots (snap_customers, snap_products) in snapshots/
- dim_customer: Surrogate key (customer_sk from stg_customers), SCD metadata cols (valid_from, valid_to, is_current), enriched metrics from int_customer_metrics via LEFT JOIN on customer_id
- dim_product: Surrogate key (product_sk from stg_products), category hierarchy aliases, markup calculations (amount and %), product_status derived column, enriched metrics from int_product_metrics
- dim_date: Static spine 2022-01-01 to 2026-12-31 using DuckDB's generate_series + unnest, YYYYMMDD integer key for BI compatibility, includes season, holiday flags, fiscal period columns
- snap_customers: check_strategy on all mutable attributes (name, contact info, address, income_bracket, cohort), natural key = customer_id, target schema = snapshots
- snap_products: check_strategy on mutable attributes (name, category, pricing, color, discontinued_date), natural key = product_id, target schema = snapshots
- Both snapshots use `invalidate_hard_deletes=False` as standard practice
- Column references verified against stg_customers (49 lines), stg_products (44 lines), int_customer_metrics (79 lines), int_product_metrics (44 lines) — all align correctly

## Task 11: fact_sales Fact Table (Completed)
- Created `dbt_project/models/marts/fact_sales.sql` as incremental model (unique_key: order_line_sk)
- Sources measures from `int_order_details` (ephemeral) — all derived measures pre-computed in intermediate
- Foreign keys resolved via LEFT JOINs to dimension tables:
  - `dim_customer` on customer_id → customer_sk
  - `dim_product` on product_id → product_sk
  - `dim_date` (x2) on order_date/ship_date → order_date_sk / ship_date_sk
- Bad data filtered: `where is_bad_data_record = 0`
- Incremental filter: `order_date >= max(order_date)` from existing table
- Created `dbt_project/models/marts/schema.yml` with schema tests for all 4 marts models:
  - dim_customer: unique/not_null on keys + email/cohort not_null
  - dim_product: unique/not_null on keys + product_name/list_price not_null
  - dim_date: unique/not_null on date_sk, date_actual + year not_null
  - fact_sales: unique/not_null on order_line_sk, FK relationships to all 3 dims, not_null on core measures, accepted_values on is_bad_data_record
- No external dbt packages used

## Task 12: obt_sales One Big Table (Completed)
- Created `dbt_project/models/marts/obt_sales.sql` as table (full refresh) materialization
- Denormalizes fact_sales with ALL dimension attributes from dim_customer, dim_product, dim_date (x2)
- Customer columns prefixed with `customer_` for ambiguous names (city, state, postal_code, country, total_orders, total_revenue)
- Product columns prefixed with `product_` for ambiguous names (list_price, standard_cost)
- Order date columns prefixed with `order_` (year, quarter, month, day-of-week, season, holiday, etc.)
- Ship date columns prefixed with `ship_` (year, month, day-of-week)
- Left joins on surrogate keys: customer_sk → customer_sk, product_sk → product_sk, order_date_sk → date_sk, ship_date_sk → date_sk
- No schema tests added — OBT data quality inherited from fact and dimension models (inline tests via Task 11's schema.yml already cover underlying models)
- No dbt_utils or external packages used

## Task 13: dbt Tests — Schema + 10 Singular Tests (Completed)
- Enhanced `dbt_project/models/marts/schema.yml` with additional column tests:
  - dim_customer: `income_bracket` accepted_values [LOW, MEDIUM, HIGH, VERY_HIGH]
  - fact_sales: `quantity` accepted_values [1-10] (range validation)
  - fact_sales: `channel` accepted_values [Online, Retail, Catalog, B2B]
  - fact_sales: `profit_margin_pct` not_null
- Created 10 singular test SQL files in `dbt_project/tests/`:
  1. `test_no_null_customer_sk_in_fact.sql` (warn) — FK integrity check
  2. `test_no_negative_quantity.sql` (error, data_quality) — catches injected bad data
  3. `test_no_zero_price_items.sql` (error, data_quality) — catches injected bad data
  4. `test_no_future_dates.sql` (error, data_quality) — catches injected bad data
  5. `test_no_duplicate_order_lines.sql` (error, data_quality) — catches injected bad data
  6. `test_profit_margin_range.sql` (warn) — business rule: -100% to 100%
  7. `test_customer_scd2_validity.sql` (warn) — SCD2 no overlapping validity periods
  8. `test_daily_sales_positive.sql` (warn) — every date in range has sales
  9. `test_dimensional_completeness.sql` (warn) — all FK values exist in dimensions
  10. `test_data_freshness.sql` (warn) — raw data not older than 30 days
- Bad data catcher tests (2-5) tagged `data_quality` with severity='error'
- Normal tests (1, 6-10) use severity='warn'
- All tests are singular tests (in tests/), not schema tests in YAML
- No dbt packages used — dependency-free

## Task 14: Metabase Setup Script & Dashboards (Completed)
- Created `metabase/setup.py` — Python script automating Metabase REST API configuration
  - Health check loop (up to 120s) before proceeding
  - First-time admin user creation via `/api/setup` using `setup-token`
  - Subsequent runs re-login via `/api/session` (idempotent)
  - DuckDB connection at `/data/warehouse/sales_analytics.duckdb` — checks for existing DB to avoid duplicates
  - Loads dashboard definitions from `metabase/dashboards/*.json` and creates cards via `/api/card` + `/api/dashboard/{id}/cards`
  - 1s rate-limit delay between card creations
  - Configurable via CLI args or env vars (MB_BASE_URL, MB_USER, MB_PASS)
- Created 3 dashboard JSONs in `metabase/dashboards/` (4 cards each, 12 total):
  - `sales_overview.json`: Revenue line, category bar, day-of-week bar, top 10 customers table
  - `product_performance.json`: Top products bar, category-area over time, profit margin scatter, category distribution pie
  - `customer_analysis.json`: Segment pie, revenue per customer bar, acquisition line, geography map
- No modifications to Dockerfile.metabase or docker-compose.yml (already set up in Task 3)

## F3 Full Integration QA (Attempt 1-2: REJECTED)
- QA scenarios executed: 8 total (4 PASS, 1 PARTIAL, 3 FAIL)
- Critical blocker: dim_date model DuckDB type incompatibility
- Issue 1: `date_part()` returns BIGINT, DATE - BIGINT invalid → fixed with CAST to INTEGER
- Issue 2: `generate_series()` returns TIMESTAMP not DATE, TIMESTAMP - INTEGER invalid → fixed with ::date cast
- Evidence saved to `.sisyphus/evidence/final-qa/`

## F3 Full Integration QA (Attempt 3: APPROVED)
- Both dim_date fixes applied successfully
- DuckDB v1.5.5 quirk: `generate_series(date, date, interval)` returns TIMESTAMP, not DATE
- All 8 dbt models build successfully, schema passes (58/58 expected), data quality catches all bad data
- Star schema fully queryable with referential integrity maintained
- Use `dbt run` then `dbt test` separately — `dbt build` skips downstream models when upstream tests fail

## Task: Documentation (Completed)
- Created README.md (291 lines), docs/architecture.md (86 lines), docs/data_dictionary.md (191 lines)
- README uses ASCII art for architecture diagrams (no mermaid) for GitHub rendering compatibility
- Architecture doc follows ADR format (Context / Decision / Trade-off / Benefits) for each choice
- Data dictionary documents all 3 layers (bronze, silver, gold) with column-level tables
- Verified project tree matches actual filesystem before writing
