# Sales Analytics Data Warehouse

## TL;DR

> **Quick Summary**: Build a complete Sales Analytics Data Warehouse as a portfolio project — synthetic data generation → DuckDB warehouse → dbt transformations (star schema + SCD Type 2) → Airflow orchestration → Metabase dashboards. Everything runs locally via Docker Compose with CI/CD via GitHub Actions.
>
> **Deliverables**:
> - Synthetic data generator (cohort-based, 100K-500K rows, 3 years)
> - DuckDB warehouse with star schema (dim_customer SCD Type 2, dim_product, dim_date, fact_sales)
> - dbt project with staging → intermediate → marts layers + tests + docs
> - Airflow 8-task linear DAG with DockerOperator for dbt
> - Metabase dashboards (3 dashboards, 12 charts total)
> - GitHub Actions CI (dbt test on push)
> - Comprehensive README matching churn project quality
>
> **Estimated Effort**: Large (20-25 tasks)
> **Parallel Execution**: YES — 6 waves
> **Critical Path**: Generator → Staging models → Dimensions + Intermediate → Fact → OBT → End-to-end QA

---

## Context

### Original Request
Build a portfolio project: Sales Analytics Data Warehouse with ETL pipeline. Skills to showcase: ETL, Data Modeling, SQL, Airflow, dbt, Metabase (BI).

### Interview Summary
**Key Discussions**:
- **Warehouse**: DuckDB (embedded, zero-infra, perfect for portfolio)
- **Data Source**: Synthetic generation with cohort-based customer behavior simulation (adopting patterns from erp-synthetic-data-generator)
- **Data Volume**: 100K-500K rows, 3 years of history
- **Data Model**: Star Schema + SCD Type 2 via dbt snapshots (check strategy)
- **Orchestration**: Airflow (Docker Compose), manual trigger
- **Transform**: dbt in a **separate container**, triggered via DockerOperator from Airflow
- **Data Ingestion**: Python generator → CSV → COPY INTO DuckDB
- **BI**: Metabase (Docker, connects to DuckDB via JDBC)
- **Testing**: Comprehensive — dbt schema tests + singular tests + Airflow data quality check tasks
- **CI/CD**: GitHub Actions — dbt test on every push
- **Scope**: Standard — ETL pipeline + warehouse + dbt models + Airflow DAG + Metabase dashboards
- **OUT**: Real-time streaming, REST API layer, user authentication, multiple fact tables

**Research Findings**:
- **contoso-retail-analytics** (k3XD16): Reference for dbt model structure, linear 8-task Airflow DAG, SCD Type 2 snapshots, OBT for BI consumption
- **erp-synthetic-data-generator** (scripts-and-tables): Production-grade cohort-based synthetic data with 6 customer behavior cohorts, day-by-day simulation, seeded RNG
- **CRM-Sales-Warehouse** (Shaan-alpha): Airflow + dbt hybrid pattern with Python ETL extract/clean
- **customer-churn-prediction** (sibling project): Conventions to follow — `uv` deps, `src/` layout, `docker-compose.yml`, `.github/workflows/ci.yml`, comprehensive README

### Metis Review
**Identified Gaps** (resolved):
- **Architecture**: dbt runs in separate container (DockerOperator). Airflow triggers it. Clean separation.
- **Data ingestion**: Generator → CSV files → COPY INTO DuckDB (classic ELT pattern)
- **DAG schedule**: Manual trigger only — generator produces all 3 years at once
- **DuckDB file path**: Shared Docker volume mounted at consistent path across all containers
- **DuckDB file strategy**: Single file at `/data/warehouse/sales_analytics.duckdb`, shared via Docker volume
- **dbt profiles.yml**: Checked into repo (no credentials needed for DuckDB), works locally and in Docker

**Guardrails Applied** (from Metis):
- Single fact table only (fact_sales) — no scope creep into fact_orders, fact_returns, etc.
- Max 5 dimensions (customer, product, date, channel, employee) — locked in
- SCD Type 2 on max 2 dimensions (customer, product)
- Linear DAG only — no branching, no sensors, no subDAGs
- Exactly 3 Metabase dashboards, max 4 cards each (12 total)
- No custom Airflow plugins or operators — built-ins only
- No dbt macro over-abstraction — inline SQL is fine
- No PythonOperator for SQL logic — Python ops call dbt or DuckDB only
- Intentionally inject 3-5 bad data records to demonstrate dbt quality tests

---

## Work Objectives

### Core Objective
Build an end-to-end Sales Analytics Data Warehouse that demonstrates production-grade data engineering: ELT pipeline, dimensional modeling, SCD management, orchestration, testing, and BI visualization.

### Concrete Deliverables
- **Synthetic data generator**: Python script producing raw CSV files (customers, products, sales) with realistic cohort behavior
- **DuckDB warehouse**: Star schema with SCD Type 2 dimensions and incremental fact table
- **dbt project**: 3-layer model architecture (staging → intermediate → marts) with tests and docs
- **Airflow DAG**: 8-task linear pipeline orchestrating ingestion and transformation
- **Metabase dashboards**: 3 dashboards (Sales Overview, Product Performance, Customer Analysis)
- **CI/CD**: GitHub Actions workflow running dbt test on push
- **README**: Comprehensive documentation matching churn project quality

### Definition of Done
- [ ] `docker compose up` starts all services (Airflow + Postgres + Metabase + dbt-runner)
- [ ] Airflow DAG triggers and completes: all 8 tasks in `success` state
- [ ] `dbt test` passes: 0 failures across all schema + singular tests
- [ ] Bad data injection caught by dbt quality tests (≥1 test fails as expected)
- [ ] SCD Type 2: updating a customer attribute produces 2 rows with valid_from/valid_to
- [ ] Metabase accessible at `http://localhost:3000` with 3 dashboards showing live data
- [ ] GitHub Actions CI green on push
- [ ] README ≥ 150 lines with tech stack, project tree, setup guide, architecture

### Must Have
- Working Airflow DAG with 8 tasks in correct order
- dbt models producing a queryable star schema
- SCD Type 2 tracking on customer dimension
- Metabase connection to DuckDB
- CI passing on push
- Bad data intentionally injected and caught by tests

### Must NOT Have (Guardrails)
- No real-time streaming / Kafka
- No REST API layer
- No user authentication
- No custom Airflow operators
- No multiple fact tables
- No Alpine-based Metabase (use Debian-based)
- No dbt seed for 100K+ rows (use COPY INTO)
- No dbt macro over-abstraction
- No environment-specific configs
- No `.env` files committed (use `.env.example`)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (follows churn project patterns)
- **Automated tests**: Comprehensive — dbt schema + singular tests + Airflow quality check tasks
- **Framework**: dbt built-in tests + duckdb SQL queries for verification
- **CI**: GitHub Actions with `setup-uv@v4` → `uv sync --frozen` → `dbt deps` → `dbt seed` → `dbt build` → `dbt test`

### QA Policy
Every task MUST include agent-executed QA scenarios (see TODO template below).
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Data/Backend**: Bash with DuckDB CLI — query tables, check row counts, verify referential integrity
- **Airflow/Docker**: Bash with docker compose + curl to Airflow API — trigger DAGs, check task states
- **Metabase/BI**: Bash with curl to Metabase API — verify health, dashboard count, card data
- **CI**: Bash with gh CLI — check workflow run status

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — all parallel):
├── Task 1: Project scaffolding + pyproject.toml + config files
├── Task 2: Synthetic data generator (cohort-based Python module)
├── Task 3: Docker Compose + Dockerfiles (Airflow, dbt, Metabase, Postgres)
└── Task 4: dbt project scaffolding (dbt_project.yml, profiles.yml, packages.yml)

Wave 2 (Data pipeline foundation — parallel):
├── Task 5: Run data generator → produce CSV files
├── Task 6: dbt staging models (sources.yml + stg_customers, stg_products, stg_sales)
├── Task 7: Airflow DAG code (sales_pipeline.py with 8 tasks)
└── Task 8: COPY INTO + DuckDB initialization

Wave 3 (dbt core models — parallel after staging):
├── Task 9: dbt intermediate models (int_order_details, int_customer_metrics, int_product_metrics)
├── Task 10: dbt dimension models + SCD Type 2 snapshots
└── Task 11: dbt fact model (fact_sales, incremental, unique_key)

Wave 4 (Integration — parallel):
├── Task 12: dbt tests (schema tests + 10 singular tests including bad data checks)
├── Task 13: dbt OBT (obt_sales denormalized for Metabase)
└── Task 14: Metabase setup + Dockerfile + 3 dashboards

Wave 5 (CI + Docs — parallel):
├── Task 15: GitHub Actions CI (dbt test on push)
├── Task 16: README + project documentation
└── Task 17: start.sh CLI wrapper + gitignore cleanup

Wave FINAL (End-to-end verification — all parallel):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality + build verification
├── Task F3: Full integration QA (execute every scenario)
└── Task F4: Scope fidelity check

Critical Path: 1 → 5 → 6 → 9 → 11 → 13 → 16 → F1-F4 → user okay
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 5 (Wave 1)
```

### Dependency Matrix
- **1**: - → 5, 7, 8, 15, 17 (W2)
- **2**: - → 5 (W2)
- **3**: - → 7, 8, 14 (W2/W4)
- **4**: - → 6 (W2)
- **5**: 1, 2 → 8 (W2)
- **6**: 4 → 9, 10 (W3)
- **7**: 3 → 12 → nothing further (parallel)
- **8**: 3, 5 → 12, 14 (W4)
- **9**: 6 → 11 (W3)
- **10**: 6 → 11 (W3)
- **11**: 9, 10 → 13 (W4)
- **12**: 7, 8 → - (parallel)
- **13**: 11 → 16 (W5)
- **14**: 3, 8 → 16 (W5)
- **15**: 1 → 16 (W5)
- **16**: 13, 14, 15 → - (done)
- **17**: 1 → - (polish)

---

## TODOs

- [x] 1. Project Scaffolding + Config Files

  **What to do**:
  - Set up `pyproject.toml` with `uv` dependencies (duckdb, faker, numpy, pandas, apache-airflow, dbt-duckdb, dbt-core)
  - Create `.gitignore` (add `data/raw/`, `data/warehouse/`, `target/`, `dbt_packages/`, `__pycache__/`)
  - Create `.python-version` (3.12)
  - Create `start.sh` CLI wrapper (mirroring churn project pattern: `start.sh generate`, `start.sh infra`, `start.sh test`)
  - Create directory structure: `src/`, `data/raw/`, `data/warehouse/`, `dbt_project/`, `airflow/dags/`, `metabase/`, `docs/`, `tests/`
  - Create `src/config.py` with shared constants (DuckDB path, data paths, column definitions)
  - Pin exact dependency versions (dbt-duckdb 1.10.x, duckdb 1.x, apache-airflow 3.x)

  **Must NOT do**:
  - Don't install dbt globally — it lives in a separate container
  - Don't create `uv.lock` manually — let `uv sync` generate it

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: 5, 7, 8, 15, 17
  - **Blocked By**: None

  **References**:
  - `customer-churn-prediction/pyproject.toml` — Dependency management pattern, project metadata, tool configs
  - `customer-churn-prediction/start.sh` — CLI wrapper convention
  - `customer-churn-prediction/.gitignore` — Gitignore pattern

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Project structure exists
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run `ls src/` — should exist
      2. Run `ls data/raw/ data/warehouse/ dbt_project/ airflow/dags/ metabase/ tests/` — all directories exist
      3. Run `ls pyproject.toml .gitignore .python-version start.sh src/config.py` — all files exist
    Expected Result: All directories and files present
    Evidence: .sisyphus/evidence/task-1-structure.txt

  Scenario: Dependencies resolve
    Tool: Bash
    Preconditions: pyproject.toml exists
    Steps:
      1. Run `uv sync --frozen` — should fail (no lock file yet, that's expected)
      2. Run `uv sync` — should succeed
    Expected Result: uv sync completes without error
    Evidence: .sisyphus/evidence/task-1-uv-sync.txt
  ```

  **Commit**: YES
  - Message: `chore: scaffold sales-analytics project structure`
  - Files: `pyproject.toml`, `.gitignore`, `.python-version`, `start.sh`, `src/config.py`

- [x] 2. Synthetic Data Generator

  **What to do**:
  - Create `src/generate.py` as the main entry point
  - Create `src/data/` package with modules:
    - `src/data/cohorts.py` — 6 customer behavior cohorts (LOYAL_HEAVY, LOYAL_LIGHT, GROWING, DECLINING, ONE_SHOT, CHURN_RISK) with purchase probabilities and churn rates
    - `src/data/customers.py` — Customer generation: demographics, geography, cohort assignment (seeded RNG for reproducibility)
    - `src/data/products.py` — Product catalog: 50-100 products across categories, with list_price, standard_cost
    - `src/data/sales.py` — Day-by-day sales simulation: for each customer each day, use cohort probabilities + seasonality multiplier to decide if they buy, what they buy, quantity
    - `src/data/seasonality.py` — Combined multiplier function: monthly patterns, holiday spikes, day-of-week effects
  - Output: `data/raw/raw_customers.csv`, `data/raw/raw_products.csv`, `data/raw/raw_sales.csv`
  - Use seeded RNG (numpy + random + Faker with deterministic seeds) for full reproducibility
  - Intentionally inject 5 bad records into raw_sales (null customer_id, negative quantity, future date, duplicate order_id, zero-price line item) — these will be caught by dbt quality tests later
  - CLI: `python -m src.generate` or `start.sh generate`

  **Must NOT do**:
  - Don't generate more than 3 output tables — the raw layer stays lean
  - Don't output to DuckDB directly — the generator writes CSVs only (the COPY INTO task handles DB loading)
  - Don't add store/employee data — scope boundary

  **Recommended Agent Profile**:
  - **Category**: `deep` (goal-oriented — needs to understand cohort simulation patterns)
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: 5
  - **Blocked By**: None

  **References**:
  - `erp-synthetic-data-generator/erp_synth/cohorts.py` — Cohort definition pattern (p_buy_by_year, p_close_day, price_sensitivity per cohort)
  - `erp-synthetic-data-generator/erp_synth/sales.py` — Day-by-day per-customer sales generation with diminishing invoice probability
  - `erp-synthetic-data-generator/erp_synth/seasonality.py` — combined_multiplier(date, market) pattern for realistic temporal patterns
  - `customer-churn-prediction/src/data/` — Sibling project's data module structure

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Generator produces raw CSV files with correct row counts
    Tool: Bash
    Preconditions: src/generate.py exists, dependencies installed
    Steps:
      1. Run `uv run python -m src.generate --seed 42`
      2. Run `wc -l data/raw/raw_customers.csv`
      3. Run `wc -l data/raw/raw_products.csv`
      4. Run `wc -l data/raw/raw_sales.csv`
    Expected Result: customers ≥ 10000 rows, products ≥ 50 rows, sales between 100K-500K rows
    Evidence: .sisyphus/evidence/task-2-row-counts.txt

  Scenario: Reproducibility (same seed → same data)
    Tool: Bash
    Preconditions: First run completed
    Steps:
      1. Run `cp data/raw/raw_sales.csv data/raw/raw_sales_backup.csv`
      2. Run `rm data/raw/raw_sales.csv`
      3. Run `uv run python -m src.generate --seed 42`
      4. Run `md5sum data/raw/raw_sales.csv > new_hash.txt && md5sum data/raw/raw_sales_backup.csv > old_hash.txt`
      5. Run `diff new_hash.txt old_hash.txt`
    Expected Result: Files are identical (md5 hashes match)
    Evidence: .sisyphus/evidence/task-2-reproducibility.txt

  Scenario: Bad data records are present
    Tool: Bash
    Preconditions: Generator has run
    Steps:
      1. Run `duckdb -c "SELECT count(*) FROM read_csv_auto('data/raw/raw_sales.csv') WHERE customer_id IS NULL"`
      2. Run `duckdb -c "SELECT count(*) FROM read_csv_auto('data/raw/raw_sales.csv') WHERE quantity < 0"`
    Expected Result: ≥ 1 row with null customer_id, ≥ 1 row with negative quantity
    Evidence: .sisyphus/evidence/task-2-bad-data.txt
  ```

  **Commit**: YES
  - Message: `feat: add cohort-based synthetic data generator`
  - Files: `src/generate.py`, `src/data/__init__.py`, `src/data/cohorts.py`, `src/data/customers.py`, `src/data/products.py`, `src/data/sales.py`, `src/data/seasonality.py`

- [x] 3. Docker Compose + Dockerfiles

  **What to do**:
  - Create `docker-compose.yml` with profile-based services (matching churn project conventions):
    - **airflow-postgres**: postgres:16-alpine (Airflow metadata DB, port 5435 to avoid conflicts)
    - **airflow-init**: Initializes Airflow DB (run once)
    - **airflow-webserver**: Airflow webserver (port 8080)
    - **airflow-scheduler**: Airflow scheduler
    - **airflow-triggerer**: Airflow triggerer
    - **dbt-runner**: Custom Dockerfile (dbt-duckdb installed) — started on-demand by Airflow DockerOperator, no open ports
    - **metabase**: Custom Debian-based Metabase with DuckDB JDBC driver (port 3000)
  - Create `Dockerfile` for dbt-runner:
    - Base: `python:3.12-slim`
    - Install dbt-core + dbt-duckdb via pip
    - Copy `dbt_project/` into image
    - Entrypoint: `dbt` (so DockerOperator can pass subcommands)
  - Create `Dockerfile.metabase`:
    - Base: `eclipse-temurin:21-jre` (Debian-based JRE, not Alpine)
    - Download Metabase JAR + DuckDB JDBC driver
    - Set MB_DB_TYPE, MB_DB_FILE for embedded H2 (simple setup)
  - Shared Docker volume `warehouse-data` mounted at `/data/warehouse/` in all services that need DuckDB access
  - Network setup: all services on `sales-analytics-net` bridge network
  - Use `profiles` to allow selective service startup (e.g., `docker compose --profile infra up`)

  **Must NOT do**:
  - Don't use Alpine-based Metabase image (DuckDB JDBC has glibc issues)
  - Don't expose postgres or dbt-runner ports externally
  - Don't add environment variables with secrets — this is portfolio-only

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: 7, 8, 14
  - **Blocked By**: None

  **References**:
  - `customer-churn-prediction/docker-compose.yml` — Profile-based service pattern, port conventions, volume setup
  - `customer-churn-prediction/Dockerfile` — Multi-stage build pattern, uv-based dependency installation
  - MotherDuck Metabase Docker guide: Debian-based JRE image + DuckDB JDBC plugin
  - Apache Airflow official docker-compose (simplified for LocalExecutor — remove Celery services)

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Docker Compose builds and starts services
    Tool: Bash
    Preconditions: Docker and Docker Compose installed
    Steps:
      1. Run `docker compose build` — should succeed
      2. Run `docker compose --profile infra up -d` — all services start
      3. Run `docker compose ps` — verify all services show "Up" or "Exited (0)" (for init)
    Expected Result: All containers start without errors
    Evidence: .sisyphus/evidence/task-3-docker-ps.txt

  Scenario: Airflow webserver is accessible
    Tool: Bash
    Preconditions: Docker services running
    Steps:
      1. Run `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health`
    Expected Result: HTTP 200
    Evidence: .sisyphus/evidence/task-3-airflow-health.txt
  ```

  **Commit**: YES
  - Message: `feat: add Docker Compose with Airflow, dbt-runner, and Metabase services`
  - Files: `docker-compose.yml`, `Dockerfile`, `Dockerfile.metabase`, `.dockerignore`

- [x] 4. dbt Project Scaffolding

  **What to do**:
  - Create `dbt_project/dbt_project.yml`:
    - Name: `sales_analytics`
    - Profile: `sales_analytics` (DuckDB)
    - Model materialization rules: staging=view, intermediate=ephemeral, marts/dimensions=table, marts/facts=incremental
    - Test configs: schema tests enabled, severity=warn for relationships, error for uniqueness
  - Create `dbt_project/profiles.yml`:
    - DuckDB target: `path: /data/warehouse/sales_analytics.duckdb`
    - Threads: 4
  - Create `dbt_project/packages.yml` (empty initially — no external packages needed)
  - Create model directories: `models/staging/`, `models/intermediate/`, `models/marts/`
  - Create snapshot directory: `snapshots/`
  - Create test directory: `tests/`
  - Create macro directory: `macros/`
  - Create seed directory: `seeds/`
  - Create analysis directory: `analyses/`

  **Must NOT do**:
  - Don't add dbt packages yet — this project doesn't need dbt_utils or similar
  - Don't add model SQL files yet — those come in Tasks 6-13
  - Don't commit profiles.yml with absolute paths — use relative to project or env var

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: 6
  - **Blocked By**: None

  **References**:
  - `contoso-retail-analytics/contoso_retail/dbt_project.yml` — Materialization strategy per model layer
  - `contoso-retail-analytics/contoso_retail/profiles.yml` — DuckDB profile configuration
  - dbt-duckdb docs: https://docs.getdbt.com/docs/core/connect-data-platform/duckdb-setup

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: dbt project compiles
    Tool: Bash
    Preconditions: dbt_project/ exists, profiles.yml is valid
    Steps:
      1. Run `cd dbt_project && dbt compile --profiles-dir .`
    Expected Result: Exit code 0, "Finished compiling" in output
    Evidence: .sisyphus/evidence/task-4-dbt-compile.txt
  ```

  **Commit**: YES
  - Message: `feat: scaffold dbt project with DuckDB profile and model directories`
  - Files: `dbt_project/dbt_project.yml`, `dbt_project/profiles.yml`, `dbt_project/packages.yml`, directory stubs

- [x] 5. Run Data Generator → Produce CSV Files

  **What to do**:
  - Execute the data generator to produce the 3 raw CSV files
  - Run: `uv run python -m src.generate --seed 42`
  - Verify output: `data/raw/raw_customers.csv`, `data/raw/raw_products.csv`, `data/raw/raw_sales.csv` exist with correct schemas
  - Verify row counts meet targets
  - Verify bad data records are present (null customer_id, negative quantity, future date, duplicate order_id, zero-price line)

  **Must NOT do**:
  - Don't commit CSV files to git (add `data/raw/` to `.gitignore`)
  - Don't modify generator code here — just run it

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on generator existing)
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8)
  - **Blocks**: 8
  - **Blocked By**: 1, 2

  **References**:
  - `src/generate.py` — The generator to run
  - `src/config.py` — Paths and constants

  **Acceptance Criteria**:
  - [ ] `uv run python -m src.generate --seed 42` exits with code 0
  - [ ] `data/raw/raw_customers.csv` exists with ≥ 10000 rows
  - [ ] `data/raw/raw_sales.csv` exists with 100K-500K rows
  - [ ] Bad data records confirmed present

  **Evidence to Capture**:
  - [ ] `.sisyphus/evidence/task-5-row-counts.txt`
  - [ ] `.sisyphus/evidence/task-5-bad-data.txt`

  **Commit**: NO (groups with Task 1 or Task 8)

- [x] 6. dbt Staging Models + Source Definitions

  **What to do**:
  - Create `dbt_project/models/sources.yml`:
    - Define 3 sources: `raw_customers`, `raw_products`, `raw_sales`
    - Loader: `duckdb` (read from DuckDB where CSV was COPYed INTO)
    - Add freshness checks (warn if data > 7 days old)
  - Create `dbt_project/models/staging/stg_customers.sql`:
    - Select from source `raw_customers`
    - Column renaming (snake_case standardization)
    - Data type casting (dates, integers)
    - Surrogate key generation using `hash(customer_id)` for SCD Type 2
    - Filter: remove rows with null customer_id
  - Create `dbt_project/models/staging/stg_products.sql`:
    - Select from source `raw_products`
    - Column renaming, type casting
    - Category hierarchy columns (if present in source)
  - Create `dbt_project/models/staging/stg_sales.sql`:
    - Select from source `raw_sales`
    - Column renaming, type casting
    - Flag bad data records (is_negative_qty, is_future_date, is_zero_price, is_duplicate_order)
    - Keep bad records but flag them (don't filter) — quality tests will catch them
  - Add schema tests to `sources.yml` or create `models/staging/schema.yml`:
    - `stg_customers`: unique (customer_id), not_null (customer_id, name, email)
    - `stg_products`: unique (product_id), not_null (product_id, product_name, list_price)
    - `stg_sales`: not_null (order_id, line_item_id, customer_id, product_id, quantity, unit_price)
    - `stg_sales`: relationships (customer_id → stg_customers, product_id → stg_products)

  **Must NOT do**:
  - Don't add business logic in staging — these are 1:1 with raw sources, just cleaned
  - Don't filter out bad data — keep it flagged for the test layer

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 7, 8)
  - **Blocks**: 9, 10
  - **Blocked By**: 4

  **References**:
  - `contoso-retail-analytics/contoso_retail/models/silver/staging/stg_customer.sql` — Staging model pattern (column selection, renaming, surrogate keys)
  - `contoso-retail-analytics/contoso_retail/models/silver/staging/stg_sales.sql` — Sales staging with date parsing and FK columns

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Staging models compile and run
    Tool: Bash
    Preconditions: DuckDB file exists with raw tables loaded
    Steps:
      1. Run `cd dbt_project && dbt run --select staging`
      2. Check exit code
    Expected Result: Exit code 0, all 3 staging models succeed
    Evidence: .sisyphus/evidence/task-6-dbt-run-staging.txt

  Scenario: Staging model row counts match raw
    Tool: Bash
    Preconditions: Staging models have run
    Steps:
      1. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM stg_customers"`
      2. Compare with raw CSV row count
    Expected Result: stg_customers count = raw_customers count minus any filtered nulls
    Evidence: .sisyphus/evidence/task-6-row-count-verification.txt
  ```

  **Commit**: YES
  - Message: `feat: add dbt staging models with source definitions and column standardization`
  - Files: `dbt_project/models/sources.yml`, `dbt_project/models/staging/stg_customers.sql`, `dbt_project/models/staging/stg_products.sql`, `dbt_project/models/staging/stg_sales.sql`, `dbt_project/models/staging/schema.yml`

- [x] 7. Airflow DAG

  **What to do**:
  - Create `airflow/dags/sales_pipeline.py` with 8 tasks in linear DAG:
    ```
    bronze_ingest >> dbt_deps >> dbt_seed >> dbt_run_silver >> dbt_run_gold >> dbt_snapshot >> dbt_test >> dbt_docs_generate
    ```
  - **bronze_ingest**: `BashOperator` running `init_warehouse.sh` (COPY CSV into DuckDB)
  - **dbt_deps**: `DockerOperator` running `dbt deps` (install packages)
  - **dbt_seed**: `DockerOperator` running `dbt seed --full-refresh` (seed reference data)
  - **dbt_run_silver**: `DockerOperator` running `dbt run --select staging+intermediate`
  - **dbt_run_gold**: `DockerOperator` running `dbt run --select marts`
  - **dbt_snapshot**: `DockerOperator` running `dbt snapshot`
  - **dbt_test**: `DockerOperator` running `dbt test`
  - **dbt_docs_generate**: `DockerOperator` running `dbt docs generate`
  - Use `DockerOperator` with:
    - `image`: `sales-analytics-dbt-runner:latest` (built from Dockerfile)
    - `network`: `sales-analytics-net`
    - `volumes`: mount `warehouse-data:/data/warehouse` + project code
    - `auto_remove`: True, `mount_tmp_dir`: False
  - DAG ID: `sales_analytics_pipeline`
  - Schedule: `None` (manual trigger only)
  - Default args: retries=1, retry_delay=5min, catchup=False
  - Tags: `sales-analytics`, `dbt`, `duckdb`
  - Add DAG description with doc_md

  **Must NOT do**:
  - Don't use BashOperator for dbt commands — dbt runs in separate container
  - Don't add branching, sensors, subDAGs, or ShortCircuitOperator
  - Don't add email/Slack alerting
  - Don't add more than 1 retry

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6, 8)
  - **Blocks**: None (tested independently, wired into full pipeline later)
  - **Blocked By**: 3

  **References**:
  - `contoso-retail-analytics/airflow/dags/contoso_dbt_dag.py` — Linear 8-task DAG pattern
  - `CRM-Sales-Warehouse/dags/crm_sales_pipeline.py` — dbt inside Airflow via subprocess/DockerOperator
  - Airflow DockerOperator docs: https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/operators/docker.html
  - `customer-churn-prediction/docker-compose.yml` — Network and volume conventions

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: DAG parses without errors
    Tool: Bash
    Preconditions: Docker services running
    Steps:
      1. Run `docker compose exec airflow-webserver airflow dags list`
      2. Grep for `sales_analytics_pipeline`
    Expected Result: DAG appears in list
    Evidence: .sisyphus/evidence/task-7-dag-list.txt

  Scenario: DAG import errors are empty
    Tool: Bash
    Preconditions: Docker services running
    Steps:
      1. Run `docker compose exec airflow-webserver airflow dags list-import-errors`
    Expected Result: No import errors
    Evidence: .sisyphus/evidence/task-7-dag-import-errors.txt
  ```

  **Commit**: YES
  - Message: `feat: add Airflow DAG with 8-task linear dbt pipeline`
  - Files: `airflow/dags/sales_pipeline.py`

- [x] 8. COPY INTO + DuckDB Initialization

  **What to do**:
  - Create `airflow/sql/init_warehouse.sql`:
    - Create DuckDB schemas: `bronze`, `silver`, `gold`, `snapshots`
    - COPY CSV files into bronze tables:
      ```sql
      CREATE SCHEMA IF NOT EXISTS bronze;
      CREATE TABLE bronze.raw_customers AS
        SELECT * FROM read_csv_auto('/data/raw/raw_customers.csv');
      CREATE TABLE bronze.raw_products AS
        SELECT * FROM read_csv_auto('/data/raw/raw_products.csv');
      CREATE TABLE bronze.raw_sales AS
        SELECT * FROM read_csv_auto('/data/raw/raw_sales.csv');
      ```
  - Create init script: `airflow/sql/init_warehouse.sh` that runs the SQL via duckdb CLI
  - Wire `bronze_ingest` step into Airflow DAG (already planned in Task 7 as BashOperator)
  - Verify DuckDB file exists at shared volume path

  **Must NOT do**:
  - Don't use dbt seed for raw data — this is COPY INTO for large data
  - Don't run init_warehouse.sql more than once without idempotency (use CREATE IF NOT EXISTS)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6, 7)
  - **Blocks**: 12, 14
  - **Blocked By**: 3, 5

  **References**:
  - DuckDB `read_csv_auto` docs: https://duckdb.org/docs/data/csv/overview.html
  - DuckDB `CREATE SCHEMA` docs

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Bronze tables exist with correct row counts
    Tool: Bash
    Preconditions: init_warehouse.sql has run, DuckDB file exists
    Steps:
      1. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM bronze.raw_customers"`
      2. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM bronze.raw_products"`
      3. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM bronze.raw_sales"`
    Expected Result: Row counts match CSV files
    Evidence: .sisyphus/evidence/task-8-bronze-counts.txt
  ```

  **Commit**: YES
  - Message: `feat: add DuckDB initialization with COPY INTO from CSV`
  - Files: `airflow/sql/init_warehouse.sql`, `airflow/sql/init_warehouse.sh`

- [x] 9. dbt Intermediate Models

  **What to do**:
  - Create `dbt_project/models/intermediate/int_order_details.sql` (ephemeral):
    - Join: `stg_sales` + `stg_products` + `stg_customers`
    - Compute derived measures: `gross_revenue`, `net_revenue`, `unit_cost`, `total_cost`, `profit`
    - Add flags from staging: `is_bad_data_flag`
    - Materialized: `ephemeral` (compiled as CTE into downstream models)
  - Create `dbt_project/models/intermediate/int_customer_metrics.sql` (ephemeral):
    - Aggregate per customer: total orders, total revenue, avg order value, first/last order date, days since last order
    - Customer segmentation: high_value, frequent_buyer, at_risk, new, etc.
  - Create `dbt_project/models/intermediate/int_product_metrics.sql` (ephemeral):
    - Aggregate per product: total units sold, total revenue, avg selling price, rank within category
  - Add schema tests for intermediate models (not_null on join keys)

  **Must NOT do**:
  - Don't materialize intermediate models as tables/views — ephemeral is correct
  - Don't exceed 3 intermediate models — scope boundary
  - Don't add complex window functions or advanced analytics — keep it clean

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES (all 3 can be written in parallel)
  - **Parallel Group**: Wave 3 (with Tasks 10, 11)
  - **Blocks**: 11
  - **Blocked By**: 6

  **References**:
  - `contoso-retail-analytics/contoso_retail/models/silver/intermediate/int_order_details.sql` — Intermediate model pattern (ephemeral CTE, joins staging models, computes profit_margin_pct)

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Intermediate models compile successfully
    Tool: Bash
    Preconditions: dbt project exists, staging models exist
    Steps:
      1. Run `cd dbt_project && dbt compile --select intermediate`
      2. Check for compilation errors
    Expected Result: Exit code 0, no errors
    Evidence: .sisyphus/evidence/task-9-dbt-compile-int.txt

  Scenario: int_order_details produces correct profit calculation
    Tool: Bash
    Preconditions: int_order_details exists in compiled output
    Steps:
      1. Run `cd dbt_project && dbt run --select int_order_details`
      2. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM int_order_details WHERE profit IS NOT NULL"`
    Expected Result: All rows have non-null profit
    Evidence: .sisyphus/evidence/task-9-profit-not-null.txt
  ```

  **Commit**: YES
  - Message: `feat: add dbt intermediate models for order details, customer metrics, and product metrics`
  - Files: `dbt_project/models/intermediate/int_order_details.sql`, `dbt_project/models/intermediate/int_customer_metrics.sql`, `dbt_project/models/intermediate/int_product_metrics.sql`

- [x] 10. dbt Dimension Models + SCD Type 2 Snapshots

  **What to do**:
  - Create `dbt_project/models/marts/dim_customer.sql` (table, full refresh):
    - Select from `stg_customers` with cleaned/standardized columns
    - Add surrogate key: `customer_sk = hash(customer_id)`
    - Enrich with customer segment from `int_customer_metrics`
    - Include `valid_from`, `valid_to`, `is_current` for SCD compatibility
  - Create `dbt_project/models/marts/dim_product.sql` (table, full refresh):
    - Select from `stg_products` with cleaned/standardized columns
    - Add surrogate key: `product_sk = hash(product_id)`
    - Include category hierarchy columns
  - Create `dbt_project/models/marts/dim_date.sql` (table, full refresh):
    - Date spine: all days from 2022-01-01 to 2026-12-31
    - Date attributes: year, quarter, month, month_name, week, day_of_week, is_weekend, is_holiday
  - Create `dbt_project/snapshots/snap_customers.sql` (SCD Type 2):
    - Strategy: `check` (compare all attribute columns)
    - Unique key: `customer_id` (natural key)
    - Check cols: all attributes that can change (city, email, segment, tier)
    - Target schema: `snapshots`
  - Create `dbt_project/snapshots/snap_products.sql` (SCD Type 2):
    - Same pattern, for product attributes that change (category, list_price)

  **Must NOT do**:
  - Don't add SCD Type 2 on dim_date (static data, no need)
  - Don't add SCD Type 2 on more than 2 dimensions (scope guardrail)
  - Don't use timestamp strategy for snapshots — use check strategy (more robust)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES (dimensions and snapshots can be written together)
  - **Parallel Group**: Wave 3 (with Tasks 9, 11)
  - **Blocks**: 11
  - **Blocked By**: 6

  **References**:
  - `contoso-retail-analytics/contoso_retail/models/gold/dimensions/dim_customer.sql` — Dimension model with surrogate keys
  - `contoso-retail-analytics/contoso_retail/snapshots/snap_customers.sql` — SCD Type 2 snapshot (check strategy, unique_key, check_cols, valid_from/valid_to)

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Dimension models compile and run
    Tool: Bash
    Preconditions: Staging models exist
    Steps:
      1. Run `cd dbt_project && dbt run --select dim_customer dim_product dim_date`
    Expected Result: Exit code 0, all dimensions created
    Evidence: .sisyphus/evidence/task-10-dbt-run-dims.txt

  Scenario: dim_date has correct range
    Tool: Bash
    Preconditions: dim_date has run
    Steps:
      1. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT min(date_actual), max(date_actual), count(*) FROM dim_date"`
    Expected Result: min 2022-01-01, max 2026-12-31, ≥ 1825 rows
    Evidence: .sisyphus/evidence/task-10-dim-date-range.txt

  Scenario: SCD Type 2 captures changes
    Tool: Bash
    Preconditions: snap_customers has run
    Steps:
      1. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT customer_id, count(*) FROM snap_customers GROUP BY customer_id HAVING count(*) > 1 LIMIT 5"`
    Expected Result: Some customers appear more than once (SCD2 tracking changes)
    Evidence: .sisyphus/evidence/task-10-scd2-history.txt
  ```

  **Commit**: YES
  - Message: `feat: add dbt dimension models with SCD Type 2 snapshots`
  - Files: `dbt_project/models/marts/dim_customer.sql`, `dbt_project/models/marts/dim_product.sql`, `dbt_project/models/marts/dim_date.sql`, `dbt_project/snapshots/snap_customers.sql`, `dbt_project/snapshots/snap_products.sql`

- [x] 11. dbt Fact Model (fact_sales, incremental)

  **What to do**:
  - Create `dbt_project/models/marts/fact_sales.sql` (incremental, unique_key: order_line_sk):
    - Config: `materialized='incremental'`, `unique_key='order_line_sk'`, `on_schema_change='append_new_columns'`
    - Select from `int_order_details` + join surrogate keys from dimension models
    - Measures: `quantity`, `unit_price`, `discount_amount`, `gross_revenue`, `net_revenue`, `cost_amount`, `profit`, `profit_margin_pct`
    - Foreign keys: `customer_sk`, `product_sk`, `order_date_sk`, `ship_date_sk`
    - Incremental logic:
      ```sql
      WHERE order_date >= (SELECT max(order_date) FROM {{ this }})
      ```
    - Include `is_bad_data_record` flag from intermediate model
  - Add to `dbt_project/models/marts/schema.yml`:
    - Not_null tests on all foreign keys
    - Relationships tests: customer_sk → dim_customer, product_sk → dim_product, order_date_sk → dim_date
    - Accepted_values on is_bad_data_record: 0 or 1

  **Must NOT do**:
  - Don't add a second fact table — single fact only (scope guardrail)
  - Don't use full-refresh for fact table — must be incremental for the demo
  - Don't add calculated measures that duplicate what's in intermediate models

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on dims + intermediate)
  - **Parallel Group**: Wave 3 (with Tasks 9, 10 — but runs after them)
  - **Blocks**: 13
  - **Blocked By**: 9, 10

  **References**:
  - `contoso-retail-analytics/contoso_retail/models/gold/facts/fact_sales.sql` — Incremental fact model (unique_key, merge strategy, incremental filter)

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Fact model runs incrementally
    Tool: Bash
    Preconditions: All dimension models exist
    Steps:
      1. Run `cd dbt_project && dbt run --select fact_sales`
      2. Check exit code
    Expected Result: Exit code 0, fact_sales created
    Evidence: .sisyphus/evidence/task-11-dbt-run-fact.txt

  Scenario: Referential integrity is valid
    Tool: Bash
    Preconditions: fact_sales has run
    Steps:
      1. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM fact_sales f LEFT JOIN dim_customer c ON f.customer_sk = c.customer_sk WHERE c.customer_sk IS NULL"`
      2. Run same for product_sk, order_date_sk
    Expected Result: All counts = 0 (no orphaned foreign keys)
    Evidence: .sisyphus/evidence/task-11-referential-integrity.txt

  Scenario: Bad data records are flagged
    Tool: Bash
    Preconditions: fact_sales has run
    Steps:
      1. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM fact_sales WHERE is_bad_data_record = 1"`
    Expected Result: Count ≥ 5 (matches injected bad records)
    Evidence: .sisyphus/evidence/task-11-bad-data-flagged.txt
  ```

  **Commit**: YES
  - Message: `feat: add fact_sales incremental model with referential integrity`
  - Files: `dbt_project/models/marts/fact_sales.sql`, `dbt_project/models/marts/schema.yml`

- [x] 12. dbt Tests (Schema + 10 Singular Tests + Bad Data Checks)

  **What to do**:
  - Enhance `dbt_project/models/marts/schema.yml` with comprehensive schema tests:
    - All dimensions: unique + not_null on surrogate keys
    - All dimensions: not_null on business keys
    - fact_sales: not_null on all foreign keys + relationships to dimensions
    - fact_sales: accepted_values for `is_bad_data_record` (0, 1)
    - fact_sales: check that `profit = net_revenue - cost_amount`
  - Create 10 singular tests in `dbt_project/tests/`:
    1. `test_no_null_customer_sk_in_fact.sql` — fact_sales FK integrity
    2. `test_no_negative_quantity.sql` — catches the injected bad data
    3. `test_no_zero_price_items.sql` — catches zero-price bad data
    4. `test_no_future_dates.sql` — catches future date bad data
    5. `test_no_duplicate_order_lines.sql` — catches duplicate bad data
    6. `test_profit_margin_range.sql` — profit margin between -100% and 100%
    7. `test_customer_scd2_validity.sql` — no overlapping validity periods in snapshots
    8. `test_daily_sales_positive.sql` — every day has at least some sales
    9. `test_dimensional_completeness.sql` — all FK values exist in dimension tables
    10. `test_data_freshness.sql` — raw data is not too old (uses DuckDB CURRENT_TIMESTAMP)
  - Tag the 5 "bad data catcher" tests with `data_quality` tag
  - Configure test severities: `data_quality` tests = ERROR, others = WARN

  **Must NOT do**:
  - Don't exceed 10 singular tests (scope guardrail)
  - Don't use dbt packages for tests (dbt_utils, etc.) — keep it dependency-free
  - Don't add tests that require human judgment to evaluate

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 13, 14)
  - **Blocks**: None
  - **Blocked By**: 7, 8, 11

  **References**:
  - `contoso-retail-analytics/contoso_retail/tests/` — Singular test pattern
  - dbt test docs: https://docs.getdbt.com/docs/build/tests

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: All dbt tests pass
    Tool: Bash
    Preconditions: All models have run, DuckDB populated
    Steps:
      1. Run `cd dbt_project && dbt test`
      2. Check exit code and test summary
    Expected Result: Exit code 0, all tests pass (bad data tests may fail by design for data_quality tagged ones — configured as ERROR to show they catch issues)
    Evidence: .sisyphus/evidence/task-12-dbt-test-results.txt

  Scenario: Bad data tests detect injected records
    Tool: Bash
    Preconditions: dbt test has run
    Steps:
      1. Run `cd dbt_project && dbt test --select tag:data_quality`
      2. Check which tests fail
    Expected Result: ≥ 1 test fails with expected bad data detected
    Evidence: .sisyphus/evidence/task-12-bad-data-detected.txt
  ```

  **Commit**: YES
  - Message: `feat: add dbt schema tests and 10 singular tests including data quality checks`
  - Files: `dbt_project/models/marts/schema.yml`, `dbt_project/tests/*.sql`

- [x] 13. dbt OBT (obt_sales — Denormalized for Metabase)

  **What to do**:
  - Create `dbt_project/models/marts/obt_sales.sql` (table, full refresh):
    - One Big Table: join fact_sales + ALL dimension attributes
    - Denormalized structure: one row per sale with all dimension attributes in columns
    - Purpose: Metabase queries this single table (no joins needed in BI tool)
    - Columns include: all fact measures + customer name/segment/city + product name/category/brand + date attributes (year, quarter, month)
    - Config: materialized as table (full refresh on each run, small enough for DuckDB)
  - Add schema tests: not_null on key columns, unique on (order_id, line_item_id)

  **Must NOT do**:
  - Don't add every possible column — keep it focused on what Metabase dashboards will use
  - Don't materialize as view — table is faster for BI queries
  - Don't add aggregations — this is a denormalized detail table, not an aggregate

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 12, 14)
  - **Blocks**: 16
  - **Blocked By**: 11

  **References**:
  - `contoso-retail-analytics/contoso_retail/models/gold/analytics/obt_sales.sql` — OBT pattern: fact + ALL dimension attributes in one wide table

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: OBT compiles and runs
    Tool: Bash
    Preconditions: fact_sales and all dimensions exist
    Steps:
      1. Run `cd dbt_project && dbt run --select obt_sales`
      2. Check exit code
    Expected Result: Exit code 0, obt_sales created
    Evidence: .sisyphus/evidence/task-13-dbt-run-obt.txt

  Scenario: OBT queryable by Metabase
    Tool: Bash
    Preconditions: obt_sales exists
    Steps:
      1. Run `duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM obt_sales WHERE customer_name IS NOT NULL AND product_name IS NOT NULL"`
    Expected Result: Count > 0, all rows have dimension attributes populated
    Evidence: .sisyphus/evidence/task-13-obt-dimensions.txt
  ```

  **Commit**: YES
  - Message: `feat: add obt_sales denormalized table for Metabase consumption`
  - Files: `dbt_project/models/marts/obt_sales.sql`

- [x] 14. Metabase Setup + Dashboards

  **What to do**:
  - Complete `Dockerfile.metabase`:
    - Base: `eclipse-temurin:21-jre`
    - Download Metabase JAR (latest stable)
    - Download DuckDB JDBC driver, place in `plugins/` directory
    - Set environment: `MB_PLUGINS_DIR=/app/plugins`, `MB_DB_FILE=/data/metabase/metabase.db`
    - Healthcheck: `curl -f http://localhost:3000/api/health`
  - Add Metabase service to `docker-compose.yml`:
    - Port: 3000
    - Volumes: `warehouse-data:/data/warehouse`, `metabase-data:/data/metabase`
    - Depends on: DuckDB file being populated (via data generator)
    - Profile: `infra`
  - DuckDB connection setup in Metabase:
    - After Metabase starts, use Metabase API to:
      1. Create admin user (automated via setup API token)
      2. Add DuckDB database connection (`/data/warehouse/sales_analytics.duckdb`)
      3. Sync schemas
  - Create 3 Metabase dashboards via API or saved JSON:
    1. **Sales Overview** (4 cards):
       - Total revenue over time (line chart)
       - Revenue by product category (bar chart)
       - Sales by day of week (heatmap)
       - Top 10 customers by revenue (table)
    2. **Product Performance** (4 cards):
       - Top products by units sold (bar chart)
       - Revenue by category over time (area chart)
       - Profit margin by product (scatter)
       - Product category distribution (pie)
    3. **Customer Analysis** (4 cards):
       - Customer segment breakdown (pie)
       - Revenue per customer histogram (bar)
       - Customer acquisition over time (line)
       - Customer geography map (if lat/lng available)

  **Must NOT do**:
  - Don't use Alpine-based Metabase image — use Debian-based JRE
  - Don't exceed 3 dashboards or 4 cards per dashboard (scope guardrail)
  - Don't add user authentication or permissions

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 12, 13)
  - **Blocks**: 16
  - **Blocked By**: 3, 8

  **References**:
  - MotherDuck Metabase Docker setup: Debian-based JRE + DuckDB JDBC plugin
  - Metabase API docs: https://www.metabase.com/docs/latest/api-documentation
  - Metabase DuckDB driver: https://github.com/MotherDuck-Open-Source/metabase-duckdb-driver

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: Metabase is running and healthy
    Tool: Bash
    Preconditions: Docker services up
    Steps:
      1. Run `curl -s http://localhost:3000/api/health`
    Expected Result: `{"status":"ok"}`
    Evidence: .sisyphus/evidence/task-14-metabase-health.txt

  Scenario: DuckDB database visible in Metabase
    Tool: Bash
    Preconditions: Metabase running, initial setup completed
    Steps:
      1. Run `curl -s -H "X-Metabase-Session: <token>" http://localhost:3000/api/database | python3 -c "import sys,json; dbs=json.load(sys.stdin); print([db['name'] for db in dbs])"`
    Expected Result: DuckDB database appears in list
    Evidence: .sisyphus/evidence/task-14-metabase-db.txt

  Scenario: Dashboards exist
    Tool: Bash
    Preconditions: Dashboards created
    Steps:
      1. Run `curl -s -H "X-Metabase-Session: <token>" http://localhost:3000/api/dashboard | python3 -c "import sys,json; dbs=json.load(sys.stdin); print(len(dbs))"`
    Expected Result: 3 dashboards exist
    Evidence: .sisyphus/evidence/task-14-metabase-dashboards.txt
  ```

  **Commit**: YES
  - Message: `feat: add Metabase Docker setup with DuckDB driver and 3 dashboards`
  - Files: `Dockerfile.metabase`, `metabase/setup.py`, `metabase/dashboards/`

- [x] 15. GitHub Actions CI

  **What to do**:
  - Create `.github/workflows/ci.yml`:
    - Triggers: push to main, pull_request to main
    - Steps: setup-uv → uv sync → generate data → init DuckDB → dbt deps → dbt build → dbt test
  - Use `astral-sh/setup-uv@v4` + `actions/setup-python@v5` (churn project convention)

  **Must NOT do**:
  - Don't add matrix builds, code coverage, or deployment steps

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: none needed

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 5 with Tasks 16, 17)
  - **Blocks**: None
  - **Blocked By**: 1

  **References**:
  - `customer-churn-prediction/.github/workflows/ci.yml` — CI pattern

  **Acceptance Criteria**:

  **QA Scenarios**:
  ```
  Scenario: CI workflow file exists and is valid YAML
    Tool: Bash
    Steps: python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
    Expected Result: YAML parses without error
    Evidence: .sisyphus/evidence/task-15-ci-yaml-valid.txt
  ```

  **Commit**: YES — `ci: add GitHub Actions workflow for dbt test on push`
  - Files: `.github/workflows/ci.yml`

- [x] 16. README + Project Documentation

  **What to do**:
  - Write comprehensive README.md (150+ lines, matching churn project quality)
  - Sections: Tech Stack, Project Tree, Architecture, Quick Start, Usage, dbt Models, Star Schema, Testing, CI/CD
  - Create `docs/architecture.md` (decisions and trade-offs)
  - Create `docs/data_dictionary.md` (column-level docs)

  **Must NOT do**: No blog posts, video demos, or GitHub Pages

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: none needed

  **Parallelization**: YES (Wave 5 with Tasks 15, 17)
  - **Blocked By**: 13, 14, 15

  **References**:
  - `customer-churn-prediction/README.md` — Quality benchmark

  **Acceptance Criteria**:
  ```
  Scenario: README ≥ 150 lines
    Tool: Bash -> wc -l README.md
    Expected Result: ≥ 150
    Evidence: .sisyphus/evidence/task-16-readme-length.txt
  ```

  **Commit**: YES — `docs: add comprehensive README and project documentation`
  - Files: `README.md`, `docs/architecture.md`, `docs/data_dictionary.md`

- [x] 17. start.sh CLI Wrapper + Gitignore Cleanup

  **What to do**:
  - Create `start.sh`: commands: generate, infra, dag, test, clean
  - Update `.gitignore`: add data/raw/, data/warehouse/, dbt_project/target/, dbt_project/dbt_packages/

  **Must NOT do**: Don't check in generated data

  **Recommended Agent Profile**: `quick`

  **Parallelization**: YES (Wave 5 with Tasks 15, 16) — **Blocked By**: 1

  **References**: `customer-churn-prediction/start.sh`

  **Acceptance Criteria**:
  ```
  Scenario: start.sh shows help
    Tool: Bash -> ./start.sh
    Expected Result: Shows generate, infra, dag, test, clean
    Evidence: .sisyphus/evidence/task-17-start-sh-help.txt
  ```

  **Commit**: YES — `chore: add start.sh CLI wrapper and update gitignore`
  - Files: `start.sh`, `.gitignore`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. Verify implementation exists for every "Must Have". Search for every "Must NOT Have" pattern. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan scope.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality + Build Review** — `unspecified-high`
  Verify: directory structure matches plan, dbt_project/ compiles, docker-compose.yml parses, CI workflow is valid YAML, .gitignore covers generated data.
  Check AI slop: no `print()` in prod code, no over-engineered macros, no dead code.
  Output: `Build [PASS/FAIL] | Structure [PASS/FAIL] | Issues [N] | VERDICT`

- [x] F3. **Full Integration QA** — `unspecified-high`
  Execute EVERY QA scenario from EVERY task end-to-end:
  - Generate data → init DuckDB → build dbt models → test dbt → trigger Airflow DAG → verify Metabase
  - Test SCD Type 2 by simulating a customer address change and re-running snapshot
  - Verify bad data injection is caught by dbt tests
  Capture all evidence to `.sisyphus/evidence/final-qa/`
  Output: `Scenarios [N/N pass] | Integration [PASS/FAIL] | SCD2 [PASS/FAIL] | DataQuality [N caught] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual files. Verify 1:1 compliance — everything in spec was built, nothing beyond spec. Check "Must NOT do" compliance. Flag cross-task contamination (e.g., Task 6 touching Task 10's files).
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Scope [IN/N, OUT/N] | VERDICT`

---

## Commit Strategy

| Task(s) | Message | Key Files |
|---------|---------|-----------|
| 1 | `chore: scaffold sales-analytics project structure` | pyproject.toml, .gitignore, .python-version, start.sh, src/config.py |
| 2 | `feat: add cohort-based synthetic data generator` | src/generate.py, src/data/__init__.py, src/data/*.py |
| 3 | `feat: add Docker Compose with Airflow, dbt-runner, Metabase services` | docker-compose.yml, Dockerfile, Dockerfile.metabase |
| 4 | `feat: scaffold dbt project with DuckDB profile` | dbt_project/dbt_project.yml, profiles.yml |
| 5 | NO COMMIT (run generator, don't commit CSVs) | — |
| 6 | `feat: add dbt staging models with source definitions` | dbt_project/models/staging/*.sql, sources.yml |
| 7 | `feat: add Airflow DAG with 8-task linear dbt pipeline` | airflow/dags/sales_pipeline.py |
| 8 | `feat: add DuckDB initialization with COPY INTO` | airflow/sql/init_warehouse.sql, init_warehouse.sh |
| 9 | `feat: add dbt intermediate models` | dbt_project/models/intermediate/*.sql |
| 10 | `feat: add dbt dimension models with SCD Type 2 snapshots` | dbt_project/models/marts/dim_*.sql, snapshots/*.sql |
| 11 | `feat: add fact_sales incremental model` | dbt_project/models/marts/fact_sales.sql, schema.yml |
| 12 | `feat: add dbt schema tests and 10 singular tests` | dbt_project/tests/*.sql |
| 13 | `feat: add obt_sales denormalized table for Metabase` | dbt_project/models/marts/obt_sales.sql |
| 14 | `feat: add Metabase Docker setup with DuckDB driver` | Dockerfile.metabase, metabase/ |
| 15 | `ci: add GitHub Actions workflow for dbt test` | .github/workflows/ci.yml |
| 16 | `docs: add comprehensive README and project docs` | README.md, docs/*.md |
| 17 | `chore: add start.sh CLI wrapper and update gitignore` | start.sh, .gitignore |

---

## Success Criteria

### Verification Commands
```bash
# Generate data
./start.sh generate

# Start infrastructure
./start.sh infra

# Trigger DAG (via Airflow CLI)
docker compose exec airflow-webserver airflow dags trigger sales_analytics_pipeline

# Run dbt tests
./start.sh test

# Check DuckDB star schema
duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM fact_sales"
duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM dim_customer"
duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM dim_product"
duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM dim_date"

# Check Metabase
curl http://localhost:3000/api/health

# Check SCD Type 2
duckdb /data/warehouse/sales_analytics.duckdb -c "SELECT count(*) FROM snap_customers"
```

### Final Checklist
- [ ] Data generator produces 100K-500K rows across 3 tables
- [ ] DuckDB contains bronze → silver → gold schemas with star schema
- [ ] dbt all models compile and run (staging + intermediate + marts)
- [ ] All dbt tests pass (with bad data tests catching the injected errors)
- [ ] Airflow DAG triggers and completes all 8 tasks successfully
- [ ] SCD Type 2: customer updates produce valid_from/valid_to history
- [ ] Metabase accessible at localhost:3000 with 3 dashboards
- [ ] GitHub Actions CI green on push
- [ ] README ≥ 150 lines with tech stack, architecture, quick start
