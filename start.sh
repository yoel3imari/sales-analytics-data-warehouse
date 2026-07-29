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
        check_prereqs uv python3
        uv run python3 -m src.generate
        ok "Synthetic data generated → data/raw/"
        ;;

    init)
        info "Initializing DuckDB warehouse from CSVs..."
        check_prereqs uv python3
        uv run python3 -m src.init_warehouse
        ok "Warehouse initialized → data/warehouse/sales.duckdb"
        ;;

    kafka)
        info "Starting Redpanda Kafka broker and Console UI..."
        check_prereqs docker
        docker compose --profile streaming up -d
        ok "Redpanda Kafka started"
        info "Kafka Broker: localhost:9092 | Console UI: http://localhost:8082"
        ;;

    produce-stream)
        info "Starting Multi-POS Real-Time Sales Producer..."
        check_prereqs uv python3
        uv run python3 -m src.streaming.producer "${@:2}"
        ;;

    consume-stream)
        info "Starting DuckDB Real-Time Stream Ingestor..."
        check_prereqs uv python3
        uv run python3 -m src.streaming.consumer "${@:2}"
        ;;

    stream-monitor)
        info "Launching Real-Time Multi-POS Terminal Dashboard..."
        check_prereqs uv python3
        uv run python3 -m src.streaming.monitor "${@:2}"
        ;;

    infra)
        info "Starting Docker infrastructure..."
        check_prereqs docker
        mkdir -p data/warehouse
        docker compose --profile infra up -d
        ok "Infrastructure started"
        info "Services: Postgres, Airflow, Metabase"
        ;;

    down)
        info "Stopping all Docker containers and removing networks..."
        check_prereqs docker
        docker compose --profile infra --profile streaming down --remove-orphans "${@:2}"
        ok "All Docker containers stopped"
        ;;

    dag)
        info "Triggering Airflow DAG..."
        check_prereqs docker
        docker compose exec airflow-webserver airflow dags unpause sales_analytics_pipeline 2>/dev/null || true
        docker compose exec airflow-webserver airflow dags trigger sales_analytics_pipeline
        ok "DAG 'sales_analytics_pipeline' triggered"
        ;;

    build)
        info "Running full dbt build..."
        check_prereqs uv python3
        (cd dbt_project && uv run dbt build --profiles-dir .)
        ok "dbt build complete"
        ;;

    test)
        info "Running dbt tests..."
        if command -v uv &>/dev/null; then
            (cd dbt_project && uv run dbt test --profiles-dir .)
        else
            check_prereqs docker
            docker compose run --rm dbt-runner dbt test --profiles-dir .
        fi
        ok "dbt tests passed"
        ;;

    setup)
        info "Running Metabase setup..."
        check_prereqs uv python3
        uv run python3 metabase/setup.py
        ok "Metabase configured"
        ;;

    clean)
        info "Cleaning generated data and warehouse..."
        rm -rf data/raw/*.csv data/warehouse/*.duckdb
        ok "Cleaned data/raw/ and data/warehouse/"
        ;;

    reset)
        info "Full reset — wiping everything and starting fresh..."
        echo ""
        echo "  Step 1: Stopping Docker containers and removing all volumes..."
        docker compose --profile infra --profile streaming down --volumes --remove-orphans 2>&1 | sed 's/^/    /'
        echo ""
        echo "  Step 2: Removing generated data files..."
        rm -rf data/raw/*.csv data/warehouse/
        echo "    Removed: data/raw/*.csv and data/warehouse/"
        echo ""
        echo "  Step 3: Recreating required directories..."
        mkdir -p data/warehouse
        echo "    Created: data/warehouse/"
        echo ""
        echo "  Step 4: Removing Docker images for clean rebuild..."
        docker rmi sales-analytics-metabase:latest sales-analytics-dbt-runner:latest 2>/dev/null || true
        echo ""
        echo -e "${GREEN}${BOLD}Reset complete.${NC}"
        echo ""
        echo "  To start fresh:"
        echo "    ./start.sh generate"
        echo "    ./start.sh infra"
        echo "    ./start.sh build"
        echo "    ./start.sh setup"
        echo "    ./start.sh dag"
        ok "Everything cleaned. Ready for fresh start."
        ;;

    *)
        echo -e "${BOLD}Sales Analytics Data Warehouse${NC}"
        echo ""
        echo "Usage: ./start.sh <command>"
        echo ""
        echo -e "${BOLD}Data Pipeline:${NC}"
        echo "  generate        Generate synthetic CSV data"
        echo "  init            Initialize DuckDB warehouse (load CSVs into bronze)"
        echo "  build           Run full dbt build (all models)"
        echo "  test            Run dbt tests"
        echo ""
        echo -e "${BOLD}Real-Time Streaming (Kafka & Multi-POS):${NC}"
        echo "  kafka           Start Redpanda Kafka broker and Console UI"
        echo "  produce-stream  Launch multi-POS sales producer (--rate 10 --duration 30)"
        echo "  consume-stream  Launch DuckDB stream ingestor consumer"
        echo "  stream-monitor  Launch live terminal POS monitoring dashboard"
        echo ""
        echo -e "${BOLD}Infrastructure:${NC}"
        echo "  infra           Start Docker services (Postgres, Airflow, Metabase)"
        echo "  down            Stop all Docker containers and infrastructure"
        echo "  dag             Trigger Airflow DAG (requires infra)"
        echo "  setup           Configure Metabase connection (requires infra)"
        echo ""
        echo -e "${BOLD}Utility:${NC}"
        echo "  clean           Remove generated data and warehouse files"
        echo "  reset           Wipe all Docker volumes, data, images — full factory reset"
        echo "  help            Show this help message"
        echo ""
        echo -e "${BOLD}Examples:${NC}"
        echo "  ./start.sh kafka           # 1. Start Redpanda Kafka container"
        echo "  ./start.sh consume-stream  # 2. Ingest stream into DuckDB bronze"
        echo "  ./start.sh produce-stream  # 3. Simulate multi-POS transactions"
        echo "  ./start.sh stream-monitor  # 4. View live POS sales dashboard"
        echo ""
        echo -e "${BOLD}Quick Start:${NC}"
        echo "  ./start.sh generate && ./start.sh infra && ./start.sh dag"
        echo ""
        echo -e "${BOLD}Reset:${NC}"
        echo "  ./start.sh reset           # Wipe everything and start fresh"
        echo "  ./start.sh generate && ./start.sh infra && ./start.sh build && ./start.sh setup"
        ;;
esac

