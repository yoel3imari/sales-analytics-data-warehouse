"""
Sales Analytics Data Warehouse Pipeline.

10-task DAG with Silver Quality Gate and Data Quality Monitoring:
1. bronze_ingest: COPY CSV data into DuckDB bronze tables
2. dbt_deps: Install dbt dependencies
3. dbt_seed: Load seed/reference data
4. dbt_run_silver: Run staging + intermediate dbt models
5. dbt_test_silver: Silver Quality Gate (circuit breaker before loading Gold)
6. dbt_run_gold: Run marts (dimensions + fact) dbt models
7. dbt_snapshot: Run dbt snapshots (SCD Type 2)
8. dbt_test_gold: Run Gold schema + integrity tests
9. dbt_test_data_quality: Run data quality anomaly checks
10. dbt_docs_generate: Generate dbt documentation
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

DBT_IMAGE = "sales-analytics-dbt-runner:latest"
NETWORK = "sales-analytics-net"
DBT_PROJECT_DIR = "/dbt_project"

logger = logging.getLogger("airflow.task")


def notify_pipeline_failure(context):
    """Callback function triggered when a pipeline task fails.
    
    Logs failure diagnostic details. In production environments, this can be
    extended to dispatch webhook notifications to Slack, PagerDuty, or Email.
    """
    task_id = context.get("task_instance").task_id
    execution_date = context.get("execution_date")
    logger.error(
        f"Pipeline Alert: Task '{task_id}' failed on {execution_date}. "
        "Check task logs for detailed diagnostic info."
    )


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_pipeline_failure,
}

with DAG(
    dag_id="sales_analytics_pipeline",
    default_args=default_args,
    description=(
        "Sales Analytics ELT: DuckDB bronze ingestion, dbt transformations "
        "(silver quality gate → gold), snapshots, tests, and docs generation"
    ),
    schedule="0 2 * * *",  # Daily at 02:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["sales-analytics", "dbt", "duckdb"],
    doc_md=r"""
# Sales Analytics Pipeline

## Overview
10-task DAG with Silver Quality Gate circuit breaker and Data Quality monitoring.

## Tasks
1. **bronze_ingest** — COPY CSV files into DuckDB bronze schema
2. **dbt_deps** — Install dbt dependencies (packages)
3. **dbt_seed** — Load seed data
4. **dbt_run_silver** — Run staging + intermediate dbt models
5. **dbt_test_silver** — Silver Quality Gate (circuit breaker)
6. **dbt_run_gold** — Run marts (dimensions + fact) dbt models
7. **dbt_snapshot** — Run SCD Type 2 snapshots
8. **dbt_test_gold** — Run Gold schema + integrity tests
9. **dbt_test_data_quality** — Run data quality anomaly checks
10. **dbt_docs_generate** — Generate dbt documentation
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
        "network_mode": NETWORK,
        "auto_remove": "success",
        "mount_tmp_dir": False,
        "docker_url": "unix://var/run/docker.sock",
        "docker_conn_id": None,
        "entrypoint": "",
        "mounts": [Mount(source="warehouse-data", target="/data/warehouse", type="volume")],
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

    dbt_test_silver = DockerOperator(
        task_id="dbt_test_silver",
        command="dbt test --profiles-dir . --select staging --exclude tag:data_quality",
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

    dbt_test_gold = DockerOperator(
        task_id="dbt_test_gold",
        command="dbt test --profiles-dir . --select marts --exclude tag:data_quality",
        **_DBT_OP_KWARGS,
    )

    dbt_test_data_quality = DockerOperator(
        task_id="dbt_test_data_quality",
        command="dbt test --profiles-dir . --select tag:data_quality",
        **_DBT_OP_KWARGS,
    )

    dbt_docs_generate = DockerOperator(
        task_id="dbt_docs_generate",
        command="dbt docs generate --profiles-dir .",
        **_DBT_OP_KWARGS,
    )

    (
        bronze_ingest
        >> dbt_deps
        >> dbt_seed
        >> dbt_run_silver
        >> dbt_test_silver
        >> dbt_run_gold
        >> dbt_snapshot
        >> dbt_test_gold
        >> dbt_test_data_quality
        >> dbt_docs_generate
    )
