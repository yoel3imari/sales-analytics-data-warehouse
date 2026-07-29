"""Unit and integration tests for real-time sales streaming."""

from __future__ import annotations

import tempfile
from pathlib import Path

import duckdb
import pytest

from src.config import POS_STORES, STREAMING_SALE_COLUMNS
from src.streaming.consumer import flush_batch_to_duckdb, init_duckdb_schema
from src.streaming.monitor import query_streaming_metrics
from src.streaming.producer import generate_pos_event, main as producer_main


def test_pos_event_structure():
    """Test that generated POS events contain all required schema fields."""
    customer_ids = ["CUST-000001", "CUST-000002"]
    products = [{"product_id": "PROD-0001", "list_price": 99.99}]
    store = POS_STORES[0]

    event = generate_pos_event(customer_ids, products, store, seq_counter=10)

    for field in STREAMING_SALE_COLUMNS:
        assert field in event, f"Missing required field {field} in POS event payload"

    assert event["store_id"] == store["store_id"]
    assert event["store_name"] == store["store_name"]
    assert event["pos_terminal_id"] in store["terminals"]
    assert event["customer_id"] in customer_ids
    assert event["product_id"] == "PROD-0001"
    assert event["quantity"] >= 1
    assert event["unit_price"] == 99.99
    assert event["discount_amount"] >= 0.0


def test_producer_dry_run():
    """Test running producer in dry-run mode (no Kafka connection required)."""
    ret = producer_main(["--dry-run", "--max-events", "10", "--rate", "100"])
    assert ret == 0


def test_duckdb_stream_ingestion_and_deduplication():
    """Test initializing DuckDB bronze streaming table and inserting micro-batches."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_sales_stream.duckdb")

        init_duckdb_schema(db_path)

        customer_ids = ["CUST-000001"]
        products = [{"product_id": "PROD-0001", "list_price": 50.0}]
        store = POS_STORES[0]

        event1 = generate_pos_event(customer_ids, products, store, seq_counter=1)
        event2 = generate_pos_event(customer_ids, products, store, seq_counter=2)

        batch = [event1, event2]

        # Flush initial batch
        inserted = flush_batch_to_duckdb(db_path, batch)
        assert inserted == 2

        # Test deduplication: re-flushing event1 should ignore duplicate primary key
        duplicate_batch = [event1]
        flush_batch_to_duckdb(db_path, duplicate_batch)

        con = duckdb.connect(db_path, read_only=True)
        count = con.execute("SELECT count(*) FROM bronze.raw_sales_stream").fetchone()[0]
        con.close()

        assert count == 2

        # Verify monitor query function
        totals, stores, recents = query_streaming_metrics(db_path)
        assert totals["total_events"] == 2
        assert len(stores) > 0
        assert len(recents) == 2

