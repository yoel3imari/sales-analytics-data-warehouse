"""Integration test for warehouse initialization logic."""

from pathlib import Path
import duckdb


def test_warehouse_connection(tmp_path):
    """Verify DuckDB can create database and bronze schema."""
    db_file = tmp_path / "test_sales.duckdb"
    conn = duckdb.connect(str(db_file))
    conn.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    conn.execute("CREATE TABLE bronze.test_tbl (id INT)")
    conn.execute("INSERT INTO bronze.test_tbl VALUES (1), (2)")
    
    count = conn.execute("SELECT count(*) FROM bronze.test_tbl").fetchone()[0]
    conn.close()
    
    assert count == 2
    assert db_file.exists()
