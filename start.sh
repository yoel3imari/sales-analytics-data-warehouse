#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

case "${1:-help}" in
    generate)
        echo "Generating synthetic data..."
        uv run python -m src.generate
        ;;
    infra)
        echo "Starting infrastructure..."
        docker compose --profile infra up -d
        ;;
    dag)
        echo "Triggering Airflow DAG..."
        docker compose exec airflow-webserver airflow dags trigger sales_analytics_pipeline
        ;;
    test)
        echo "Running dbt tests..."
        cd dbt_project && dbt test --profiles-dir .
        ;;
    clean)
        echo "Cleaning generated data and warehouse..."
        rm -rf data/raw/*.csv data/warehouse/*.duckdb
        echo "Cleaned."
        ;;
    *)
        echo "Usage: ./start.sh <command>"
        echo ""
        echo "Commands:"
        echo "  generate    Generate synthetic data (CSV files)"
        echo "  infra       Start Docker infrastructure"
        echo "  dag         Trigger Airflow DAG (requires infra)"
        echo "  test        Run dbt tests (requires infra + populated data)"
        echo "  clean       Remove generated data and warehouse"
        ;;
esac
