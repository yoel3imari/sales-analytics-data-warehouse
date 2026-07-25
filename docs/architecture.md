# Architecture Decision Record

## Technology Choices

### DuckDB over Snowflake/BigQuery

- **Context**: Portfolio project needs zero-cost hosting. Cloud warehouses require accounts, credits, and configuration that add friction to "clone and run" demos.
- **Decision**: DuckDB, an embedded OLAP database.
- **Trade-off**: Single-node, no concurrency support. Can't handle multiple simultaneous query writers. But that's fine for a single-pipeline demo.
- **Benefits**: Zero cloud costs, instant startup, full SQL support, single-file storage at `data/warehouse/sales_analytics.duckdb`. Anyone can clone the repo and run it locally without signing up for anything.

### dbt in a Separate Container

- **Context**: Airflow orchestrates the pipeline and needs to trigger dbt transformations.
- **Decision**: dbt runs in a dedicated Docker container (`Dockerfile`), triggered via Airflow's `DockerOperator`.
- **Trade-off**: Extra container to build and manage. But the alternative (installing dbt directly in the Airflow image) couples the two tools and makes independent updates harder.
- **Benefits**: Clean separation of concerns. dbt environment is isolated, can be rebuilt independently, and matches how production teams typically run dbt alongside Airflow.

### Single Fact Table

- **Context**: Scope guardrail from design review. A sales analytics project could easily spiral into multiple fact tables (orders, returns, inventory movements).
- **Decision**: One fact table (`fact_sales`) covering all sales transactions.
- **Trade-off**: Can't analyze orders and returns as separate grains. But this is a portfolio project, and a focused scope keeps the data model clear and understandable.
- **Benefits**: Simpler lineage, easier to reason about, and the OBT layer on top means the BI tool never has to navigate complex joins.

### SCD Type 2 via dbt Snapshots

- **Context**: Need to track historical changes to customer and product attributes over time.
- **Decision**: dbt snapshots with `check` strategy on both `snap_customers` and `snap_products`.
- **Trade-off**: Only captures changes between snapshot runs. If an attribute changes twice between runs, only the final state is recorded. Not fully real-time, but acceptable for a batch pipeline.
- **Benefits**: Built into dbt, no custom logic needed. `dbt_valid_from` / `dbt_valid_to` / `is_current` columns are auto-managed. The `check` strategy compares all mutable attributes in a single pass.

### COPY INTO vs dbt Seed

- **Context**: Loading 100K to 500K rows of raw CSV data into DuckDB.
- **Decision**: DuckDB's `COPY INTO` via `read_csv_auto` for bronze table loading.
- **Trade-off**: Extra step before dbt models run (handled by `init_warehouse.sql`). dbt `seed` would be simpler but is significantly slower at this volume and doesn't handle schema inference.
- **Benefits**: DuckDB's bulk CSV loading is extremely fast, `read_csv_auto` handles type detection, and the SQL-based approach is easy to understand and modify.

## Data Flow

1. **Generation**: Python script (`src/generate.py`) produces seeded CSV files with deterministic RNG
2. **Ingestion**: `COPY INTO` loads CSVs into DuckDB bronze tables via `airflow/sql/init_warehouse.sql`
3. **Staging**: dbt creates views in silver schema, 1:1 with bronze but cleaned and typed
4. **Intermediate**: dbt creates ephemeral CTEs with joins, aggregations, and derived metrics
5. **Marts**: dbt creates tables in gold schema forming the star schema
6. **Snapshots**: dbt tracks SCD Type 2 changes for customer and product dimensions
7. **Testing**: dbt validates schema constraints, integrity rules, and data quality checks
8. **BI**: Metabase queries the OBT for dashboard visualization

## Docker Architecture

All services run under a single `infra` profile:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| airflow-postgres | postgres:16 | - | Airflow metadata store |
| airflow-init | custom | - | One-time admin user creation |
| airflow-webserver | apache/airflow | 8080 | Airflow UI |
| airflow-scheduler | apache/airflow | - | Task scheduling (LocalExecutor) |
| airflow-triggerer | apache/airflow | - | Deferrable operator support |
| dbt-runner | custom | - | dbt CLI (on-demand via DockerOperator) |
| metabase | custom | 3000 | BI tool with DuckDB JDBC driver |

Shared Docker volumes:

- `warehouse-data`: Mounted by dbt-runner and metabase to access the DuckDB file
- `metabase-data`: Persists Metabase application metadata across restarts

## Design Patterns

### Bronze / Silver / Gold Layering

The pipeline follows the medallion architecture pattern:

- **Bronze** (raw): Untouched CSV data loaded into DuckDB. Source of truth for raw ingestion.
- **Silver** (staging + intermediate): Cleaned, typed, joined. Views for 1:1 mapping, ephemeral CTEs for business logic.
- **Gold** (marts): Final analytical tables. Star schema dimensions and fact table, plus the denormalized OBT for BI consumption.

### One Big Table (OBT)

The `obt_sales` model denormalizes `fact_sales` with all attributes from every dimension. This trades storage for query simplicity. Metabase doesn't need to know about joins, surrogate keys, or dimension tables. It just queries one wide table with friendly column names.

### Bad Data Injection

Five intentionally corrupted records are injected into the raw sales data during generation. These are caught by four `data_quality`-tagged singular dbt tests with `severity='error'`. This demonstrates the testing pipeline's ability to catch real data quality issues.
