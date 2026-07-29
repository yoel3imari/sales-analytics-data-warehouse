"""Multi-POS real-time sales event producer for Kafka.

Simulates multiple Point-of-Sale (POS) locations generating real-time
sales transaction streams and publishing JSON messages to Kafka.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError

from src.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_SALES_TOPIC,
    POS_STORES,
    RAW_CUSTOMERS,
    RAW_PRODUCTS,
)

logger = logging.getLogger("src.streaming.producer")

_PAYMENT_METHODS = ["Credit Card", "Debit Card", "Mobile Pay", "Cash", "Gift Card"]
_PAYMENT_PROBS = [0.55, 0.25, 0.12, 0.05, 0.03]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the POS producer."""
    parser = argparse.ArgumentParser(
        description="Multi-POS Real-Time Sales Event Producer for Kafka",
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
        help=f"Kafka topic to publish sales events (default: {KAFKA_SALES_TOPIC})",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=5.0,
        help="Target total message generation rate in events/sec (default: 5.0)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Run duration in seconds (0 for infinite, default: 0)",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Maximum total events to emit (0 for unlimited, default: 0)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible event generation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate events and log to console without pushing to Kafka",
    )
    return parser.parse_args(argv)


def _load_reference_ids() -> tuple[list[str], list[dict]]:
    """Load customer IDs and product catalog from generated CSVs or fallbacks."""
    customer_ids: list[str] = []
    products: list[dict] = []

    if Path(RAW_CUSTOMERS).exists():
        try:
            df_cust = pd.read_csv(RAW_CUSTOMERS, usecols=["customer_id"])
            customer_ids = df_cust["customer_id"].dropna().tolist()
        except Exception as err:
            logger.warning("Failed to load %s: %s", RAW_CUSTOMERS, err)

    if not customer_ids:
        customer_ids = [f"CUST-{i:06d}" for i in range(1, 101)]

    if Path(RAW_PRODUCTS).exists():
        try:
            df_prod = pd.read_csv(
                RAW_PRODUCTS,
                usecols=["product_id", "list_price"],
            )
            products = df_prod.to_dict("records")
        except Exception as err:
            logger.warning("Failed to load %s: %s", RAW_PRODUCTS, err)

    if not products:
        products = [
            {"product_id": f"PROD-{i:04d}", "list_price": round(15.0 + i * 5.5, 2)}
            for i in range(1, 21)
        ]

    return customer_ids, products


def generate_pos_event(
    customer_ids: list[str],
    products: list[dict],
    store_meta: dict,
    seq_counter: int,
) -> dict:
    """Generate a single realistic POS sale transaction payload."""
    now = datetime.now(timezone.utc)
    event_id = f"evt_{uuid.uuid4().hex[:12]}"

    # Select store & terminal
    store_id = store_meta["store_id"]
    store_name = store_meta["store_name"]
    pos_terminal = random.choice(store_meta["terminals"])
    channel = store_meta["channel"]

    # Select random customer & product
    customer_id = random.choice(customer_ids)
    product = random.choice(products)
    product_id = product["product_id"]
    unit_price = float(product.get("list_price", 29.99))

    # Quantity & discount
    quantity = random.choices([1, 2, 3, 4, 5], weights=[0.60, 0.25, 0.10, 0.03, 0.02])[0]
    discount_pct = random.choices([0.0, 0.05, 0.10, 0.20], weights=[0.75, 0.12, 0.08, 0.05])[0]
    discount_amount = round(quantity * unit_price * discount_pct, 2)

    order_id = f"STREAM-{store_id}-{now.strftime('%Y%m%d')}-{seq_counter:06d}"
    line_item_id = 1
    payment_method = random.choices(_PAYMENT_METHODS, weights=_PAYMENT_PROBS)[0]

    return {
        "event_id": event_id,
        "order_id": order_id,
        "line_item_id": line_item_id,
        "order_date": now.strftime("%Y-%m-%d"),
        "store_id": store_id,
        "store_name": store_name,
        "pos_terminal_id": pos_terminal,
        "customer_id": customer_id,
        "product_id": product_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_amount": discount_amount,
        "ship_date": now.strftime("%Y-%m-%d"),
        "ship_city": store_meta["ship_city"],
        "ship_state": store_meta["ship_state"],
        "ship_country": store_meta["ship_country"],
        "channel": channel,
        "payment_method": payment_method,
        "created_at": now.isoformat(),
    }


def is_host_resolvable(server: str) -> bool:
    """Check if server hostname can be resolved via DNS."""
    host = server.split(":")[0]
    try:
        import socket
        socket.getaddrinfo(host, None)
        return True
    except (socket.gaierror, OSError):
        return False


def create_producer(bootstrap_servers: str) -> KafkaProducer | None:
    """Initialize KafkaProducer with error handling and DNS pre-check."""
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
            producer = KafkaProducer(
                bootstrap_servers=[server],
                api_version=(2, 8, 0),
                key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
            logger.info("Connected to Kafka bootstrap server: %s", server)
            return producer
        except Exception as err:
            logger.debug("Could not connect to Kafka at %s: %s", server, err)

    logger.error("Failed to connect to any Kafka bootstrap servers: %s", resolvable_servers)
    return None


def main(argv: list[str] | None = None) -> int:
    """Run POS sales event producer loop."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    args = parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)

    customer_ids, products = _load_reference_ids()
    logger.info("Loaded %d customer IDs and %d products.", len(customer_ids), len(products))

    producer: KafkaProducer | None = None
    if not args.dry_run:
        producer = create_producer(args.bootstrap_servers)
        if producer is None:
            logger.error("Exiting due to Kafka connection failure. Use --dry-run for offline testing.")
            return 1

    interval = 1.0 / max(args.rate, 0.1)
    start_time = time.time()
    total_events = 0
    seq_counter = 1

    logger.info("=" * 60)
    logger.info("Starting Multi-POS Real-Time Sales Producer")
    logger.info("  Topic: %s", args.topic)
    logger.info("  Stores: %d locations", len(POS_STORES))
    logger.info("  Target Rate: %.1f msgs/sec", args.rate)
    logger.info("  Dry Run: %s", args.dry_run)
    logger.info("=" * 60)

    try:
        while True:
            # Check duration limit
            elapsed = time.time() - start_time
            if args.duration > 0 and elapsed >= args.duration:
                logger.info("Reached target duration limit of %d seconds.", args.duration)
                break

            # Check max events limit
            if args.max_events > 0 and total_events >= args.max_events:
                logger.info("Reached target event count limit of %d events.", args.max_events)
                break

            # Pick POS store
            store = random.choice(POS_STORES)
            event = generate_pos_event(customer_ids, products, store, seq_counter)

            if args.dry_run:
                logger.info("[DRY-RUN POS EVENT] Store: %s | Order: %s | Amount: $%.2f",
                            event["store_name"], event["order_id"],
                            event["quantity"] * event["unit_price"] - event["discount_amount"])
            elif producer is not None:
                store_id_key = event["store_id"]
                producer.send(args.topic, key=store_id_key, value=event)

            total_events += 1
            seq_counter += 1

            if total_events % 20 == 0:
                logger.info("Published %d events (rate: %.1f ev/s)", total_events, total_events / max(elapsed, 0.1))

            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Producer stopped by user signal.")
    finally:
        if producer is not None:
            producer.flush(timeout=5)
            producer.close()
            logger.info("Kafka producer flushed and closed.")

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("Producer Session Finished:")
    logger.info("  Total Events: %d", total_events)
    logger.info("  Elapsed Time: %.2f seconds", elapsed)
    logger.info("  Average Throughput: %.2f ev/s", total_events / max(elapsed, 0.001))
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
