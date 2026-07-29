# Sales Analytics Data Warehouse

End-to-end data engineering pipeline demonstrating batch ELT, **real-time event streaming with Apache Kafka (Redpanda)**, dimensional modeling, SCD management, orchestration, testing, and BI visualization.

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Warehouse** | [DuckDB](https://duckdb.org/) | Embedded OLAP database, zero-config, columnar, single-file storage |
| **Streaming Broker** | [Redpanda (Kafka API)](https://redpanda.com/) | High-performance, lightweight Kafka-compatible streaming event engine |
| **Streaming UI** | [Redpanda Console](https://redpanda.com/) | Real-time topic, partition, and payload visual management |
| **Transform** | [dbt](https://www.getdbt.com/) | Data transformation with staging, intermediate, and marts layers |
| **Orchestration** | [Apache Airflow](https://airflow.apache.org/) | 10-task linear DAG with DockerOperator and Silver Quality Gate |
| **BI** | [Metabase](https://www.metabase.com/) | Self-service BI with 3 dashboards, 12 cards |
| **Data Gen & POS Stream** | Python (Faker, NumPy, Kafka) | Cohort-based synthetic batch generator + Multi-POS real-time streaming producer |
| **Monitor UI** | Python (Rich) | Interactive terminal dashboard for live multi-POS streaming revenue & throughput |
| **Container** | Docker Compose | All services (Airflow, Postgres, Metabase, Redpanda) in reproducible containers |
| **CI/CD** | GitHub Actions | dbt build + test + streaming verification on every push |
| **Language** | Python 3.12 | Core pipeline logic, streaming engine, and data generation |

## Project Tree

```
sales-analytics/
├── airflow/
│   ├── dags/
│   │   └── sales_pipeline.py          # 10-task linear Airflow DAG with Silver Gate
│   └── sql/
│       ├── init_warehouse.sql         # DuckDB schema + COPY INTO + raw_sales_stream
│       └── init_warehouse.sh          # Shell wrapper for DuckDB init
├── dbt_project/
│   ├── dbt_project.yml                # dbt configuration
│   ├── profiles.yml                   # DuckDB connection profile
│   ├── models/
│   │   ├── sources.yml                # Raw data source definitions (batch + stream)
│   │   ├── staging/                   # Silver layer (views)
│   │   │   ├── stg_customers.sql
│   │   │   ├── stg_products.sql
│   │   │   └── stg_sales.sql          # Unified batch + POS stream model
│   │   ├── intermediate/              # Silver layer (ephemeral CTEs)
│   │   │   ├── int_order_details.sql  # Includes store & streaming attributes
│   │   │   ├── int_customer_metrics.sql
│   │   │   └── int_product_metrics.sql
│   │   └── marts/                     # Gold layer (tables)
│   │       ├── dim_customer.sql
│   │       ├── dim_product.sql
│   │       ├── dim_date.sql
│   │       ├── fact_sales.sql         # Incremental fact with POS store dimensions
│   │       └── obt_sales.sql          # Denormalized for BI
│   ├── snapshots/
│   │   ├── snap_customers.sql         # SCD Type 2
│   │   └── snap_products.sql          # SCD Type 2
│   └── tests/                         # dbt quality & business logic tests
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
│   ├── generate.py                    # CLI entry point (batch synthetic generator)
│   ├── init_warehouse.py              # CLI entry point (warehouse schema init)
│   ├── config.py                      # Shared constants & streaming POS config
│   ├── data/
│   │   ├── cohorts.py                 # 6 customer behavior cohorts
│   │   ├── customers.py               # Customer generation
│   │   ├── products.py                # Product catalog
│   │   ├── sales.py                   # Day-by-day sales simulation
│   │   └── seasonality.py             # Temporal multiplier
│   └── streaming/                     # Real-time POS streaming package
│       ├── __init__.py
│       ├── producer.py                # Multi-POS sales event producer (Kafka)
│       ├── consumer.py                # Micro-batch DuckDB stream ingestor
│       └── monitor.py                 # Real-time console terminal UI (Rich)
├── tests/                             # Pytest suite (includes test_streaming.py)
├── docker-compose.yml                 # All services (infra + streaming profiles)
├── Dockerfile                         # dbt-runner image
├── Dockerfile.metabase                # Metabase with DuckDB JDBC
├── start.sh                           # CLI wrapper script
├── pyproject.toml                     # Python dependencies (uv)
└── .github/workflows/ci.yml           # GitHub Actions CI
```

## Architecture

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                          Data Flow Architecture                          │
 └──────────────────────────────────────────────────────────────────────────┘

  [ Batch Path ]                                  [ Real-Time Streaming Path ]
  Synthetic Data Generator (Python)               Multi-POS Sales Event Producer
         │                                         (NYC, LA, Chicago, London, Web)
         ▼ CSV Files                                      │
  ┌──────────────────┐                                    ▼ JSON Events
  │  Bronze (batch)  │ COPY INTO                         ┌────────────────────────┐
  │  - raw_customers │ DuckDB                            │ Redpanda Kafka Broker  │
  │  - raw_products  │                                   │ (port 9092, UI: 8082)  │
  │  - raw_sales     │                                   └───────────┬────────────┘
  └────────┬─────────┘                                               │
           │                                                         ▼ Micro-batch ingest
           │                                             ┌────────────────────────┐
           │                                             │ DuckDB Stream Ingestor │
           │                                             │ - raw_sales_stream     │
           │                                             └───────────┬────────────┘
           │                                                         │
           └───────────────────────────┬─────────────────────────────┘
                                       │
                                       ▼ dbt run --select staging
                              ┌──────────────────┐
                              │  Silver (staging)│  stg_sales (UNION ALL batch + stream)
                              │  - stg_customers │
                              │  - stg_products  │
                              │  - stg_sales     │
                              └────────┬─────────┘
                                       │
                                       ▼ dbt run --select intermediate
                              ┌──────────────────┐
                              │  Silver (interm.)│  Ephemeral CTEs, derived metrics
                              │  - int_order_det.│  Includes POS store & terminal attributes
                              └────────┬─────────┘
                                       │
                                       ▼ dbt run --select marts
                              ┌──────────────────┐
                              │  Gold (marts)    │  Star Schema + OBT
                              │  - dim_customer  │  SCD Type 2 via snapshot
                              │  - dim_product   │  SCD Type 2 via snapshot
                              │  - dim_date      │
                              │  - fact_sales    │  Incremental with POS store keys
                              │  - obt_sales     │  Denormalized for BI
                              └────────┬─────────┘
                                       │
                                       ▼ Metabase queries OBT
                              ┌──────────────────┐
                              │  Metabase BI     │  3 dashboards, 12 cards
                              └──────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker and Docker Compose (for Airflow, Redpanda, and Metabase)

### 1. Batch Data Pipeline

```bash
# Generate synthetic batch CSV data
./start.sh generate

# Initialize DuckDB database and load raw bronze tables
./start.sh init

# Run full dbt build (staging → intermediate → marts + tests)
./start.sh build

# Run all dbt quality tests
./start.sh test
```

### 2. Real-Time Streaming Sales (Kafka & Multi-POS)

Demonstrate multiple Point-of-Sale (POS) locations continuously publishing real-time transaction streams into DuckDB:

```bash
# 1. Start Redpanda Kafka Broker & Console UI
./start.sh kafka
# Console UI available at http://localhost:8082

# 2. In a terminal: Start DuckDB Stream Ingestor
./start.sh consume-stream

# 3. In a second terminal: Start Multi-POS Sales Generator
./start.sh produce-stream --rate 10 --duration 60

# 4. In a third terminal: Launch Live Real-Time Monitoring Dashboard
./start.sh stream-monitor
```

### 3. Docker Infrastructure (Airflow + Metabase + Kafka)

```bash
# Start all containers in background
./start.sh infra

# Stop all containers
./start.sh down
```

### 4. Access Metabase & Trigger Airflow

```bash
# Metabase automated configuration:
./start.sh setup
# Access BI at http://localhost:3000 (admin@example.com / SalesAnalytics2026!)

# Trigger Airflow DAG:
./start.sh dag
# Access Airflow UI at http://localhost:8080 (admin/admin)
```

---

## Data Model

### Star Schema

```
┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│  dim_customer│◄───│   fact_sales   │───►│  dim_product   │
│  (SCD Type 2)│    │ (batch+stream) │    │  (SCD Type 2)  │
└──────────────┘    └───┬───┬───┬────┘    └────────────────┘
                        │   │   │
                        ▼   ▼   ▼
                   ┌────────────────┐
                   │   dim_date (x2)│
                   │ (order/ship)   │
                   └────────────────┘

┌──────────────────────────────────────────────────────┐
│                  obt_sales (One Big Table)           │
│ Denormalized: fact + POS store + all dimension attributes│
│ Optimized for Metabase (no BI-side joins)            │
└──────────────────────────────────────────────────────┘ 
```

### Real-Time POS Store Attributes

Real-time streaming records enrich the sales model with location and terminal lineage:
- `store_id` (e.g. `STORE-101`, `STORE-102`)
- `store_name` (e.g. `NYC Flagship POS`, `LA Downtown POS`, `London Store POS`)
- `pos_terminal_id` (e.g. `POS-101-A`, `POS-WEB-01`)
- `payment_method` (e.g. `Credit Card`, `Mobile Pay`, `Cash`)
- `is_streaming` (Flag: `1` for live stream POS, `0` for batch history)

---

## Testing Strategy

| Layer | Test Type | Count | Purpose |
|-------|-----------|-------|---------|
| **Python** | Unit & Integration | 12 | Tests cohorts, generator, warehouse init, and streaming producer/consumer |
| **dbt Schema** | `unique`, `not_null` | ~45 | Structural integrity |
| **dbt Schema** | `relationships` | 5 | Foreign key integrity |
| **dbt Schema** | `accepted_values` | 5 | Domain & channel validation (including POS channels) |
| **dbt Singular** | Data quality (ERROR) | 4 | Catch injected bad data records |
| **dbt Singular** | Business rules (WARN) | 6 | Ongoing metric monitoring |

---

## CI/CD

GitHub Actions runs on every push to `main`:

1. Install dependencies via `uv`
2. Generate synthetic batch data
3. Initialize DuckDB warehouse
4. Execute real-time streaming unit & integration tests (`pytest tests/`)
5. Run `dbt build` (all models)
6. Run `dbt test` (schema + data quality tests)

---

## Scope

### In Scope

- Real-time streaming sales pipeline with **Apache Kafka (Redpanda)**
- Multi-POS store location generator (threads/async)
- Micro-batch continuous DuckDB ingestion consumer (`bronze.raw_sales_stream`)
- Interactive live terminal monitor (`rich`)
- Unified batch + real-time streaming dbt transformations
- DuckDB data warehouse with star schema and SCD Type 2
- Airflow 10-task DAG with Silver Quality Gate circuit breaker
- 3 Metabase dashboards with 12 charts
- GitHub Actions CI

---

## License

MIT. Portfolio project for demonstration purposes.
