# Sales Analytics Data Warehouse

End-to-end data engineering pipeline demonstrating ELT, dimensional modeling, SCD management, orchestration, testing, and BI visualization.

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Warehouse** | [DuckDB](https://duckdb.org/) | Embedded OLAP database, zero-config, columnar, single-file storage |
| **Transform** | [dbt](https://www.getdbt.com/) | Data transformation with staging, intermediate, and marts layers |
| **Orchestration** | [Apache Airflow](https://airflow.apache.org/) | 8-task linear DAG with DockerOperator |
| **BI** | [Metabase](https://www.metabase.com/) | Self-service BI with 3 dashboards, 12 cards |
| **Data Gen** | Python (Faker, NumPy) | Cohort-based synthetic data generator |
| **Container** | Docker Compose | All services in reproducible containers |
| **CI/CD** | GitHub Actions | dbt build + test on every push |
| **Language** | Python 3.12 | Core logic and data generation |

## Project Tree

```
sales-analytics/
├── airflow/
│   ├── dags/
│   │   └── sales_pipeline.py          # 8-task linear Airflow DAG
│   └── sql/
│       ├── init_warehouse.sql         # DuckDB schema + COPY INTO
│       └── init_warehouse.sh          # Shell wrapper for DuckDB init
├── dbt_project/
│   ├── dbt_project.yml                # dbt configuration
│   ├── profiles.yml                   # DuckDB connection profile
│   ├── models/
│   │   ├── sources.yml                # Raw data source definitions
│   │   ├── staging/                   # Silver layer (views)
│   │   │   ├── stg_customers.sql
│   │   │   ├── stg_products.sql
│   │   │   └── stg_sales.sql
│   │   ├── intermediate/              # Silver layer (ephemeral CTEs)
│   │   │   ├── int_order_details.sql
│   │   │   ├── int_customer_metrics.sql
│   │   │   └── int_product_metrics.sql
│   │   └── marts/                     # Gold layer (tables)
│   │       ├── dim_customer.sql
│   │       ├── dim_product.sql
│   │       ├── dim_date.sql
│   │       ├── fact_sales.sql
│   │       └── obt_sales.sql
│   ├── snapshots/
│   │   ├── snap_customers.sql         # SCD Type 2
│   │   └── snap_products.sql          # SCD Type 2
│   └── tests/
│       ├── test_no_negative_quantity.sql
│       ├── test_no_zero_price_items.sql
│       ├── test_no_future_dates.sql
│       ├── test_no_duplicate_order_lines.sql
│       ├── test_no_null_customer_sk_in_fact.sql
│       ├── test_profit_margin_range.sql
│       ├── test_customer_scd2_validity.sql
│       ├── test_daily_sales_positive.sql
│       ├── test_dimensional_completeness.sql
│       └── test_data_freshness.sql
├── data/
│   ├── raw/                           # Generated CSV files (gitignored)
│   └── warehouse/                     # DuckDB database (gitignored)
├── metabase/
│   ├── setup.py                       # Automated Metabase API setup
│   └── dashboards/
│       ├── sales_overview.json
│       ├── product_performance.json
│       └── customer_analysis.json
├── src/
│   ├── generate.py                    # CLI entry point (data generation)
│   ├── init_warehouse.py              # CLI entry point (warehouse init)
│   ├── config.py                      # Shared constants
│   └── data/
│       ├── cohorts.py                 # 6 customer behavior cohorts
│       ├── customers.py               # Customer generation
│       ├── products.py                # Product catalog
│       ├── sales.py                   # Day-by-day sales simulation
│       └── seasonality.py             # Temporal multiplier
├── docker-compose.yml                 # All services (infra profile)
├── Dockerfile                         # dbt-runner image
├── Dockerfile.metabase                # Metabase with DuckDB JDBC
├── start.sh                           # CLI wrapper
├── pyproject.toml                     # Python dependencies
└── .github/workflows/ci.yml           # GitHub Actions CI
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Flow Architecture                    │
└─────────────────────────────────────────────────────────────┘

  Synthetic Data Generator (Python)
         │
         ▼  CSV files
  ┌──────────────────┐
  │  Bronze (raw)     │  COPY INTO DuckDB
  │  - raw_customers  │
  │  - raw_products   │
  │  - raw_sales      │
  └────────┬─────────┘
           │
           ▼  dbt run --select staging
  ┌──────────────────┐
  │  Silver (staging) │  Views, 1:1 with raw, cleaned
  │  - stg_customers  │
  │  - stg_products   │
  │  - stg_sales      │
  └────────┬─────────┘
           │
           ▼  dbt run --select intermediate
  ┌──────────────────┐
  │  Silver (interm.) │  Ephemeral CTEs, joined + calculated
  │  - int_order_det. │
  │  - int_cust_met.  │
  │  - int_prod_met.  │
  └────────┬─────────┘
           │
           ▼  dbt run --select marts
  ┌──────────────────┐
  │  Gold (marts)     │  Tables, star schema + OBT
  │  - dim_customer   │  SCD Type 2 via snapshot
  │  - dim_product    │  SCD Type 2 via snapshot
  │  - dim_date       │
  │  - fact_sales     │  Incremental
  │  - obt_sales      │  Denormalized for BI
  └────────┬─────────┘
           │
           ▼  Metabase queries OBT
  ┌──────────────────┐
  │  Metabase         │  3 dashboards, 12 cards
  │  - Sales Overview │
  │  - Product Perf.  │
  │  - Customer Anal. │
  └──────────────────┘
```

### Airflow DAG

```
bronze_ingest -> dbt_deps -> dbt_seed -> dbt_run_silver ->
-> dbt_run_gold -> dbt_snapshot -> dbt_test -> dbt_docs_generate
```

All dbt commands run in the `sales-analytics-dbt-runner` Docker container via Airflow's DockerOperator. The bronze_ingest step loads CSVs into DuckDB via BashOperator.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker and Docker Compose (for Airflow + Metabase)

### 1. Generate Data

```bash
./start.sh generate
# Or directly:
uv run python3 -m src.generate --seed 42
```

### 2. Initialize Warehouse

```bash
./start.sh init
# Or directly:
uv run python3 -m src.init_warehouse
```

### 3. Run dbt

```bash
cd dbt_project
dbt deps --profiles-dir .
dbt build --profiles-dir .
dbt test --profiles-dir .
```

### 4. Docker Infrastructure (Airflow + Metabase)

```bash
docker compose --profile infra up -d
```

### 5. Access Metabase

```bash
# Open http://localhost:3000
# Automated setup:
python metabase/setup.py
```

### 6. Trigger Airflow DAG

```bash
docker compose exec airflow-webserver airflow dags trigger sales_analytics_pipeline
```

## Data Model

### Star Schema

```
┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│  dim_customer │◄───│   fact_sales   │───►│  dim_product   │
│  (SCD Type 2) │    │  (incremental) │    │  (SCD Type 2)  │
└──────────────┘    └───┬───┬───┬────┘    └────────────────┘
                       │   │   │
                       ▼   ▼   ▼
                 ┌────────────────┐
                 │   dim_date (x2)│
                 │ (order/ship)   │
                 └────────────────┘

┌──────────────────────────────────────────────────────┐
│                  obt_sales (One Big Table)            │
│ Denormalized: fact + all dimension attributes         │
│ Optimized for Metabase (no BI-side joins)            │
└──────────────────────────────────────────────────────┘
```

### SCD Type 2

- **Customers**: Tracks changes to name, email, address, income_bracket, cohort
- **Products**: Tracks changes to price, cost, category, status
- Strategy: `check` (compares all attribute columns)
- Each change creates a new row with `dbt_valid_from` / `dbt_valid_to`

## Testing Strategy

| Layer | Test Type | Count | Purpose |
|-------|-----------|-------|---------|
| Schema | `unique`, `not_null` | ~20 | Structural integrity |
| Schema | `relationships` | 5 | Foreign key integrity |
| Schema | `accepted_values` | 4 | Domain validation |
| Singular | Data quality (ERROR) | 4 | Catch injected bad data |
| Singular | Business rules (WARN) | 6 | Ongoing monitoring |

**Bad Data Injection**: 5 intentionally corrupted records are added to the raw sales data to demonstrate that data quality tests catch issues:

- Null customer_id
- Negative quantity
- Future order date
- Duplicate order + line
- Zero unit price

## CI/CD

GitHub Actions runs on every push to `main`:

1. Install dependencies via `uv`
2. Generate synthetic data
3. Initialize DuckDB warehouse
4. Run `dbt deps`
5. Run `dbt build` (all models)
6. Run `dbt test` (schema tests, expected to pass)
7. Run `dbt test --select tag:data_quality` (expected to catch injected bad data)

## Scope

### In Scope

- DuckDB data warehouse with star schema
- Synthetic data generator (cohort-based, 100K to 500K rows)
- 3-layer dbt model architecture (staging, intermediate, marts)
- SCD Type 2 on 2 dimensions (customer, product)
- Airflow 8-task linear DAG
- 3 Metabase dashboards with 12 charts
- 10 dbt singular tests including data quality checks
- GitHub Actions CI

### Out of Scope

- Real-time streaming / Kafka
- REST API layer
- User authentication
- Multiple fact tables
- Custom Airflow operators
- Environment-specific configs

## License

MIT. Portfolio project for demonstration purposes.
