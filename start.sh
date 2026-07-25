#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors (only when terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' BOLD='' NC=''
fi

info()  { echo -e "${BLUE}ℹ${NC}  $*"; }
ok()    { echo -e "${GREEN}✓${NC}  $*"; }
warn()  { echo -e "${YELLOW}⚠${NC}  $*"; }
fail()  { echo -e "${RED}✗${NC}  $*"; exit 1; }

check_prereqs() {
    local missing=0
    for cmd in "$@"; do
        if ! command -v "$cmd" &>/dev/null; then
            fail "Required command not found: $cmd"
        fi
    done
}

case "${1:-help}" in
    generate)
        info "Generating synthetic data..."
        check_prereqs uv python
        uv run python -m src.generate
        ok "Synthetic data generated → data/raw/"
        ;;

    init)
        info "Initializing DuckDB warehouse from CSVs..."
        check_prereqs uv python
        uv run python -m src.init_warehouse
        ok "Warehouse initialized → data/warehouse/sales.duckdb"
        ;;

    infra)
        info "Starting Docker infrastructure..."
        check_prereqs docker
        docker compose --profile infra up -d
        ok "Infrastructure started"
        info "Services: Postgres, Airflow, Metabase"
        ;;

    dag)
        info "Triggering Airflow DAG..."
        check_prereqs docker
        docker compose exec airflow-webserver airflow dags trigger sales_analytics_pipeline
        ok "DAG 'sales_analytics_pipeline' triggered"
        ;;

    build)
        info "Running full dbt build..."
        check_prereqs docker
        docker compose exec airflow-webserver bash -c "cd /opt/airflow/dbt_project && dbt build --profiles-dir ."
        ok "dbt build complete"
        ;;

    test)
        info "Running dbt tests..."
        check_prereqs docker
        docker compose exec airflow-webserver bash -c "cd /opt/airflow/dbt_project && dbt test --profiles-dir ."
        ok "dbt tests passed"
        ;;

    setup)
        info "Running Metabase setup..."
        check_prereqs uv python
        uv run python metabase/setup.py
        ok "Metabase configured"
        ;;

    clean)
        info "Cleaning generated data and warehouse..."
        rm -rf data/raw/*.csv data/warehouse/*.duckdb
        ok "Cleaned data/raw/ and data/warehouse/"
        ;;

    *)
        echo -e "${BOLD}Sales Analytics Data Warehouse${NC}"
        echo ""
        echo "Usage: ./start.sh <command>"
        echo ""
        echo -e "${BOLD}Data Pipeline:${NC}"
        echo "  generate    Generate synthetic CSV data"
        echo "  init        Initialize DuckDB warehouse (load CSVs into bronze)"
        echo "  build       Run full dbt build (all models)"
        echo "  test        Run dbt tests"
        echo ""
        echo -e "${BOLD}Infrastructure:${NC}"
        echo "  infra       Start Docker services (Postgres, Airflow, Metabase)"
        echo "  dag         Trigger Airflow DAG (requires infra)"
        echo "  setup       Configure Metabase connection"
        echo ""
        echo -e "${BOLD}Utility:${NC}"
        echo "  clean       Remove generated data and warehouse files"
        echo "  help        Show this help message"
        echo ""
        echo -e "${BOLD}Examples:${NC}"
        echo "  ./start.sh generate     # Step 1: Create synthetic data"
        echo "  ./start.sh init         # Step 2: Load into DuckDB"
        echo "  ./start.sh infra        # Start Docker services"
        echo "  ./start.sh dag          # Run Airflow pipeline"
        echo "  ./start.sh build        # Run all dbt models"
        echo ""
        echo -e "${BOLD}Quick Start:${NC}"
        echo "  ./start.sh generate && ./start.sh infra && ./start.sh dag"
        ;;
esac
