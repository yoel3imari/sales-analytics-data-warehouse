"""
Sales Analytics Data Warehouse Pipeline.

Linear 8-task DAG that orchestrates the ELT pipeline:
1. bronze_ingest: COPY CSV data into DuckDB bronze tables
2. dbt_deps: Install dbt dependencies
3. dbt_seed: Load seed/reference data
4. dbt_run_silver: Run staging + intermediate dbt models
5. dbt_run_gold: Run marts (dimensions + fact) dbt models
6. dbt_snapshot: Run dbt snapshots (SCD Type 2)
7. dbt_test: Run all dbt tests
8. dbt_docs_generate: Generate dbt documentation

All dbt commands run via DockerOperator using the sales-analytics-dbt-runner
image. The bronze_ingest step runs via BashOperator with DuckDB CLI.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator

DBT_IMAGE = "sales-analytics-dbt-runner:latest"
NETWORK = "sales-analytics-net"
DBT_PROJECT_DIR = "/dbt_project"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="sales_analytics_pipeline",
    default_args=default_args,
    description=(
        "Sales Analytics ELT: DuckDB bronze ingestion, dbt transformations "
        "(silver→gold), snapshots, tests, and docs generation"
    ),
    schedule=None,  # Manual trigger only
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["sales-analytics", "dbt", "duckdb"],
    doc_md=r"""
# Sales Analytics Pipeline

## Overview
Linear 8-task DAG for the Sales Analytics Data Warehouse.
Orchestrates data ingestion and dbt transformation pipeline.

## Tasks
1. **bronze_ingest** — COPY CSV files into DuckDB bronze schema
2. **dbt_deps** — Install dbt dependencies (packages)
3. **dbt_seed** — Load seed data
4. **dbt_run_silver** — Run staging + intermediate dbt models
5. **dbt_run_gold** — Run marts (dimensions + fact) dbt models
6. **dbt_snapshot** — Run SCD Type 2 snapshots
7. **dbt_test** — Run all dbt schema + singular tests
8. **dbt_docs_generate** — Generate dbt documentation

## Execution
Trigger manually via Airflow UI or CLI:
```bash
airflow dags trigger sales_analytics_pipeline
```
""",
) as dag:

    bronze_ingest = BashOperator(
        task_id="bronze_ingest",
        bash_command="""
        echo "=== Bronze Ingestion: COPY CSV into DuckDB ==="
        duckdb /data/warehouse/sales_analytics.duckdb < /opt/airflow/sql/init_warehouse.sql
        echo "=== Bronze Ingestion Complete ==="
        """,
    )

    # ── Shared DockerOperator kwargs for dbt tasks ──
    _DBT_OP_KWARGS = {
        "image": DBT_IMAGE,
        "network": NETWORK,
        "auto_remove": True,
        "mount_tmp_dir": False,
        "docker_url": "unix://var/run/docker.sock",
        "docker_conn_id": None,
        "entrypoint": "",  # Override the image's ENTRYPOINT ["dbt"]
        # Mount the shared warehouse-data volume so dbt can read/write the
        # DuckDB file. The dbt project code is baked into the image at
        # /dbt_project/ via the Dockerfile COPY.
        "volumes": ["warehouse-data:/data/warehouse"],
        "environment": {
            "DBT_PROFILES_DIR": DBT_PROJECT_DIR,
        },
    }

    dbt_deps = DockerOperator(
        task_id="dbt_deps",
        command="dbt deps --profiles-dir .",
        **_DBT_OP_KWARGS,
    )

    dbt_seed = DockerOperator(
        task_id="dbt_seed",
        command="dbt seed --profiles-dir . --full-refresh",
        **_DBT_OP_KWARGS,
    )

    dbt_run_silver = DockerOperator(
        task_id="dbt_run_silver",
        command="dbt run --profiles-dir . --select staging+intermediate",
        **_DBT_OP_KWARGS,
    )

    dbt_run_gold = DockerOperator(
        task_id="dbt_run_gold",
        command="dbt run --profiles-dir . --select marts",
        **_DBT_OP_KWARGS,
    )

    dbt_snapshot = DockerOperator(
        task_id="dbt_snapshot",
        command="dbt snapshot --profiles-dir .",
        **_DBT_OP_KWARGS,
    )

    dbt_test = DockerOperator(
        task_id="dbt_test",
        command="dbt test --profiles-dir .",
        **_DBT_OP_KWARGS,
    )

    dbt_docs_generate = DockerOperator(
        task_id="dbt_docs_generate",
        command="dbt docs generate --profiles-dir .",
        **_DBT_OP_KWARGS,
    )

    bronze_ingest >> dbt_deps >> dbt_seed >> dbt_run_silver >> dbt_run_gold >> dbt_snapshot >> dbt_test >> dbt_docs_generate
