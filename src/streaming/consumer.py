"""Real-time Kafka consumer and DuckDB stream ingestor.

Consumes multi-POS sales events from Kafka and appends micro-batches
into the DuckDB bronze layer table ``bronze.raw_sales_stream``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from src.config import DUCKDB_PATH, KAFKA_BOOTSTRAP_SERVERS, KAFKA_SALES_TOPIC

logger = logging.getLogger("src.streaming.consumer")

CREATE_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.raw_sales_stream (
    event_id VARCHAR PRIMARY KEY,
    order_id VARCHAR,
    line_item_id BIGINT,
    order_date DATE,
    store_id VARCHAR,
    store_name VARCHAR,
    pos_terminal_id VARCHAR,
    customer_id VARCHAR,
    product_id VARCHAR,
    quantity BIGINT,
    unit_price DOUBLE,
    discount_amount DOUBLE,
    ship_date DATE,
    ship_city VARCHAR,
    ship_state VARCHAR,
    ship_country VARCHAR,
    channel VARCHAR,
    payment_method VARCHAR,
    created_at TIMESTAMP
);
"""

INSERT_EVENT_SQL = """
INSERT INTO bronze.raw_sales_stream (
    event_id, order_id, line_item_id, order_date, store_id, store_name,
    pos_terminal_id, customer_id, product_id, quantity, unit_price,
    discount_amount, ship_date, ship_city, ship_state, ship_country,
    channel, payment_method, created_at
) VALUES (
    ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?,
    ?, ?, ?
) ON CONFLICT (event_id) DO NOTHING;
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the stream consumer."""
    parser = argparse.ArgumentParser(
        description="Real-Time Kafka Consumer for DuckDB Warehouse Ingestion",
    )
    parser.add_argument(
        "--bootstrap-servers",
        type=str,
        default=",".join(KAFKA_BOOTSTRAP_SERVERS),
        help=f"Kafka bootstrap servers (default: {','.join(KAFKA_BOOTSTRAP_SERVERS)})",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=KAFKA_SALES_TOPIC,
        help=f"Kafka topic (default: {KAFKA_SALES_TOPIC})",
    )
    parser.add_argument(
        "--group-id",
        type=str,
        default="duckdb-sales-ingestor",
        help="Kafka consumer group ID (default: duckdb-sales-ingestor)",
    )
    parser.add_argument(
        "--duckdb-path",
        type=str,
        default=DUCKDB_PATH,
        help=f"DuckDB database file path (default: {DUCKDB_PATH})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Micro-batch size for DuckDB flush (default: 50)",
    )
    parser.add_argument(
        "--flush-interval",
        type=float,
        default=2.0,
        help="Maximum time in seconds between flushes (default: 2.0)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Run duration in seconds (0 for infinite, default: 0)",
    )
    return parser.parse_args(argv)


def init_duckdb_schema(db_path: str) -> None:
    """Ensure bronze schema and raw_sales_stream table exist in DuckDB."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path)
    try:
        con.execute(CREATE_TABLE_SQL)
        logger.info("DuckDB schema `bronze.raw_sales_stream` verified at %s", db_path)
    finally:
        con.close()


def is_host_resolvable(server: str) -> bool:
    """Check if server hostname can be resolved via DNS."""
    host = server.split(":")[0]
    try:
        import socket
        socket.getaddrinfo(host, None)
        return True
    except (socket.gaierror, OSError):
        return False


def create_consumer(bootstrap_servers: str, topic: str, group_id: str) -> KafkaConsumer | None:
    """Initialize KafkaConsumer with server fallback and DNS pre-check."""
    server_list = [s.strip() for s in bootstrap_servers.split(",") if s.strip()]
    resolvable_servers = [s for s in server_list if is_host_resolvable(s)]

    if not resolvable_servers:
        logger.error(
            "None of the configured Kafka bootstrap servers (%s) are DNS resolvable.",
            server_list,
        )
        return None

    for server in resolvable_servers:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=[server],
                api_version=(2, 8, 0),
                group_id=group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=1000,
            )
            logger.info("Kafka consumer connected to %s (topic: %s)", server, topic)
            return consumer
        except Exception as err:
            logger.debug("Failed connecting consumer to %s: %s", server, err)

    logger.error("Consumer failed to connect to any Kafka servers in %s", resolvable_servers)
    return None


def flush_batch_to_duckdb(db_path: str, batch: list[dict]) -> int:
    """Write micro-batch of events to DuckDB raw_sales_stream table."""
    if not batch:
        return 0

    con = duckdb.connect(db_path)
    inserted = 0
    try:
        rows = []
        for e in batch:
            rows.append((
                e.get("event_id"),
                e.get("order_id"),
                e.get("line_item_id", 1),
                e.get("order_date"),
                e.get("store_id"),
                e.get("store_name"),
                e.get("pos_terminal_id"),
                e.get("customer_id"),
                e.get("product_id"),
                e.get("quantity"),
                e.get("unit_price"),
                e.get("discount_amount", 0.0),
                e.get("ship_date"),
                e.get("ship_city"),
                e.get("ship_state"),
                e.get("ship_country"),
                e.get("channel"),
                e.get("payment_method"),
                e.get("created_at"),
            ))
        con.executemany(INSERT_EVENT_SQL, rows)
        inserted = len(rows)
        logger.info("Flushed %d streaming events → bronze.raw_sales_stream", inserted)
    except Exception as err:
        logger.error("Error inserting micro-batch into DuckDB: %s", err)
    finally:
        con.close()

    return inserted


def main(argv: list[str] | None = None) -> int:
    """Run stream consumer loop."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    args = parse_args(argv)

    # Prepare DuckDB schema
    init_duckdb_schema(args.duckdb_path)

    consumer = create_consumer(args.bootstrap_servers, args.topic, args.group_id)
    if consumer is None:
        logger.error("Could not start consumer. Ensure Kafka/Redpanda service is running.")
        return 1

    buffer: list[dict] = []
    last_flush_time = time.time()
    total_ingested = 0
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("DuckDB Real-Time Stream Ingestor Active")
    logger.info("  Target DB: %s", args.duckdb_path)
    logger.info("  Batch size: %d | Max flush interval: %.1fs", args.batch_size, args.flush_interval)
    logger.info("=" * 60)

    try:
        while True:
            elapsed = time.time() - start_time
            if args.duration > 0 and elapsed >= args.duration:
                logger.info("Reached duration limit of %d seconds.", args.duration)
                break

            # Poll messages
            msg_batch = consumer.poll(timeout_ms=500)
            for topic_partition, msgs in msg_batch.items():
                for msg in msgs:
                    if isinstance(msg.value, dict):
                        buffer.append(msg.value)

            now = time.time()
            if len(buffer) >= args.batch_size or (now - last_flush_time >= args.flush_interval and buffer):
                flushed = flush_batch_to_duckdb(args.duckdb_path, buffer)
                total_ingested += flushed
                buffer.clear()
                last_flush_time = now

    except KeyboardInterrupt:
        logger.info("Consumer shutdown requested.")
    finally:
        if buffer:
            flushed = flush_batch_to_duckdb(args.duckdb_path, buffer)
            total_ingested += flushed
        consumer.close()
        logger.info("Consumer closed.")

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("Ingestion Summary:")
    logger.info("  Total Ingested Events: %d", total_ingested)
    logger.info("  Duration: %.2f seconds", elapsed)
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
