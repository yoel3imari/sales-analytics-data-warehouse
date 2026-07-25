#!/usr/bin/env bash
# ============================================================
# Warehouse Initialization Script
#
# Runs init_warehouse.sql against the DuckDB database.
# Used by Airflow's bronze_ingest BashOperator task.
#
# Falls back to Python duckdb module if CLI is unavailable.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="/data/warehouse/sales_analytics.duckdb"
SQL_FILE="${SCRIPT_DIR}/init_warehouse.sql"

echo "=== Warehouse Initialization ==="
echo "Database: ${DB_PATH}"
echo "SQL file: ${SQL_FILE}"
echo ""

if [ ! -f "${DB_PATH}" ]; then
    echo "Creating new DuckDB database at ${DB_PATH}..."
    mkdir -p "$(dirname "${DB_PATH}")"
    touch "${DB_PATH}"
fi

# Prefer duckdb CLI; fall back to Python duckdb module
if command -v duckdb &>/dev/null; then
    echo "Using duckdb CLI..."
    duckdb "${DB_PATH}" < "${SQL_FILE}"
elif python3 -c "import duckdb" &>/dev/null; then
    echo "duckdb CLI not found — falling back to Python duckdb module..."
    python3 - <<PYEOF
import duckdb

conn = duckdb.connect("${DB_PATH}")
with open("${SQL_FILE}") as f:
    sql = f.read()
conn.execute(sql)
conn.close()
PYEOF
else
    echo "ERROR: Neither duckdb CLI nor Python duckdb module available." >&2
    exit 1
fi

echo ""
echo "=== Warehouse Initialization Complete ==="
