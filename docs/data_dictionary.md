# Data Dictionary

## Source Layer (Bronze)

### raw_customers

| Column | Type | Description |
|--------|------|-------------|
| customer_id | VARCHAR | Unique customer identifier (CUST-XXXXX) |
| first_name | VARCHAR | Customer first name |
| last_name | VARCHAR | Customer last name |
| email | VARCHAR | Email address |
| phone | VARCHAR | Phone number |
| address_line1 | VARCHAR | Street address |
| address_line2 | VARCHAR | Apartment or suite (optional) |
| city | VARCHAR | City |
| state | VARCHAR | State abbreviation |
| postal_code | VARCHAR | ZIP code |
| country | VARCHAR | Country (always USA) |
| birth_date | DATE | Date of birth |
| gender | VARCHAR | M or F |
| income_bracket | VARCHAR | LOW, MEDIUM, HIGH, or VERY_HIGH |
| cohort | VARCHAR | One of: LOYAL_HEAVY, LOYAL_LIGHT, GROWING, DECLINING, ONE_SHOT, CHURN_RISK |
| signup_date | DATE | Date customer signed up |
| last_update_date | DATE | Last profile update date |

### raw_products

| Column | Type | Description |
|--------|------|-------------|
| product_id | VARCHAR | Unique product identifier (PROD-XXXXX) |
| product_name | VARCHAR | Product name |
| category | VARCHAR | Product category |
| subcategory | VARCHAR | Product subcategory |
| brand | VARCHAR | Brand name |
| list_price | DECIMAL(10,2) | Standard selling price |
| standard_cost | DECIMAL(10,2) | Cost to acquire or manufacture |
| color | VARCHAR | Product color |
| size | VARCHAR | Size (S, M, L, XL, or N/A) |
| weight_kg | DECIMAL(8,2) | Weight in kilograms |
| launch_date | DATE | Product launch date |
| discontinued_date | DATE | Discontinuation date (nullable) |

### raw_sales

| Column | Type | Description |
|--------|------|-------------|
| order_id | VARCHAR | Order identifier (ORD-XXXXXXXX) |
| line_item_id | INTEGER | Line item number within the order |
| order_date | DATE | Order placement date |
| customer_id | VARCHAR | Foreign key to customers |
| product_id | VARCHAR | Foreign key to products |
| quantity | INTEGER | Units ordered |
| unit_price | DECIMAL(10,2) | Price per unit after discount |
| discount_amount | DECIMAL(10,2) | Total discount applied to this line item |
| ship_date | DATE | Shipment date |
| ship_city | VARCHAR | Shipping city |
| ship_state | VARCHAR | Shipping state |
| ship_country | VARCHAR | Shipping country |
| channel | VARCHAR | Online, Retail, Catalog, or B2B |

## Staging Layer (Silver)

### stg_customers

Staging view, 1:1 mapping with `raw_customers`. Adds `customer_sk` (md5 hash surrogate key) and cleans text fields (trim, normalize casing).

### stg_products

Staging view, 1:1 mapping with `raw_products`. Adds `product_sk` (md5 hash surrogate key) and casts price columns to proper decimal types.

### stg_sales

Staging view, 1:1 mapping with `raw_sales`. Adds `order_line_sk` (composite md5 of order_id + line_item_id) and flags bad data rows:

| Flag Column | Type | Description |
|-------------|------|-------------|
| is_null_customer | INTEGER | 1 if customer_id is null |
| is_negative_quantity | INTEGER | 1 if quantity is negative |
| is_future_date | INTEGER | 1 if order_date is in the future |
| is_zero_price | INTEGER | 1 if unit_price is zero |
| is_bad_data_record | INTEGER | 1 if ANY of the above flags is true |

## Intermediate Layer (Silver, Ephemeral)

### int_order_details

Joins `stg_sales` + `stg_products` + `stg_customers`. Computes derived financial measures:

| Column | Type | Description |
|--------|------|-------------|
| gross_revenue | DECIMAL | quantity * unit_price |
| net_revenue | DECIMAL | gross_revenue - discount_amount |
| total_cost | DECIMAL | quantity * standard_cost |
| gross_profit | DECIMAL | gross_revenue - total_cost |
| net_profit | DECIMAL | net_revenue - total_cost |
| profit_margin_pct | DECIMAL | (net_profit / gross_revenue) * 100 |

### int_customer_metrics

Customer-level aggregations derived from order history:

| Column | Type | Description |
|--------|------|-------------|
| total_orders | INTEGER | Count of distinct orders |
| total_revenue | DECIMAL | Sum of net_revenue |
| avg_order_value | DECIMAL | total_revenue / total_orders |
| value_segment | VARCHAR | Based on total_revenue thresholds |
| frequency_segment | VARCHAR | Based on order count |
| recency_segment | VARCHAR | Based on days since last order |
| customer_tier | VARCHAR | Overall tier from combined segments |

### int_product_metrics

Product-level aggregations derived from sales history:

| Column | Type | Description |
|--------|------|-------------|
| total_units_sold | INTEGER | Sum of quantity |
| total_revenue | DECIMAL | Sum of net_revenue |
| total_profit | DECIMAL | Sum of net_profit |
| revenue_rank | INTEGER | Rank by total_revenue |
| volume_rank | INTEGER | Rank by total_units_sold |
| profit_rank | INTEGER | Rank by total_profit |
| margin_rank | INTEGER | Rank by profit_margin_pct |

## Marts Layer (Gold)

### dim_customer

Star schema dimension for customers. Surrogate key (`customer_sk`) from `stg_customers`. Enriched with segmentation metrics from `int_customer_metrics` via LEFT JOIN on `customer_id`.

Tracks SCD Type 2 changes via `snap_customers` snapshot. Mutable attributes: name, email, phone, address fields, income_bracket, cohort.

### dim_product

Star schema dimension for products. Surrogate key (`product_sk`) from `stg_products`. Includes category hierarchy aliases, markup calculations (amount and percentage), and a derived `product_status` column.

Enriched with ranking metrics from `int_product_metrics`. Tracks SCD Type 2 changes via `snap_products` snapshot. Mutable attributes: name, category, pricing, color, discontinued_date.

### dim_date

Static date dimension covering 2022-01-01 through 2026-12-31. Generated using DuckDB's `generate_series` + `unnest`.

| Column | Type | Description |
|--------|------|-------------|
| date_sk | INTEGER | YYYYMMDD integer key (BI compatibility) |
| date_actual | DATE | Full date value |
| year | INTEGER | Calendar year |
| quarter | INTEGER | Calendar quarter (1-4) |
| month | INTEGER | Calendar month (1-12) |
| day_of_week | VARCHAR | Monday through Sunday |
| season | VARCHAR | Winter, Spring, Summer, Fall |
| is_holiday | BOOLEAN | Holiday flag |
| fiscal_period | VARCHAR | Fiscal year/quarter designation |

### fact_sales

Incremental fact table. Sources measures from `int_order_details`. Foreign keys resolved via LEFT JOINs to all three dimension tables:

- `customer_sk` from `dim_customer` on `customer_id`
- `product_sk` from `dim_product` on `product_id`
- `order_date_sk` from `dim_date` on `order_date`
- `ship_date_sk` from `dim_date` on `ship_date`

Bad data rows filtered out (`is_bad_data_record = 0`). Incremental strategy appends only new records based on `order_date`.

### obt_sales

Denormalized "One Big Table" combining `fact_sales` with ALL attributes from every dimension. Table materialization (full refresh).

Column naming conventions for disambiguation:

- `customer_*` prefix for customer dimension columns that overlap with fact measures (city, state, postal_code, country, total_orders, total_revenue)
- `product_*` prefix for product dimension columns that overlap (list_price, standard_cost)
- `order_*` prefix for order date attributes (year, quarter, month, day_of_week, season, holiday)
- `ship_*` prefix for ship date attributes (year, month, day_of_week)

Contains approximately 80 columns. Optimized for Metabase consumption with zero BI-side joins required.

## Snapshots (SCD Type 2)

### snap_customers

Targets the `snapshots` schema. Uses `check` strategy comparing all mutable customer attributes. Natural key: `customer_id`. Hard deletes disabled (`invalidate_hard_deletes = false`).

### snap_products

Targets the `snapshots` schema. Uses `check` strategy comparing all mutable product attributes. Natural key: `product_id`. Hard deletes disabled.

Both snapshots produce standard SCD Type 2 metadata columns: `dbt_valid_from`, `dbt_valid_to`, `dbt_scd_id`, `dbt_updated_at`.
