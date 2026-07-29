"""Real-time Multi-POS Sales Terminal Dashboard.

Monitors streaming POS transactions in DuckDB and presents a live
console summary using Rich tables and metrics.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.config import DUCKDB_PATH

console = Console()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for monitor."""
    parser = argparse.ArgumentParser(
        description="Real-Time Multi-POS Sales Terminal Dashboard",
    )
    parser.add_argument(
        "--duckdb-path",
        type=str,
        default=DUCKDB_PATH,
        help=f"DuckDB database file path (default: {DUCKDB_PATH})",
    )
    parser.add_argument(
        "--refresh-rate",
        type=float,
        default=1.0,
        help="Dashboard refresh interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Monitor duration in seconds (0 for infinite, default: 0)",
    )
    return parser.parse_args(argv)


def query_streaming_metrics(db_path: str) -> tuple[dict, list[dict], list[dict]]:
    """Query live metrics from DuckDB bronze.raw_sales_stream."""
    total_metrics = {"total_events": 0, "total_revenue": 0.0, "avg_order_value": 0.0}
    store_metrics: list[dict] = []
    recent_events: list[dict] = []

    if not Path(db_path).exists():
        return total_metrics, store_metrics, recent_events

    try:
        con = duckdb.connect(db_path, read_only=True)
        try:
            # Check table exists
            table_check = con.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'bronze' AND table_name = 'raw_sales_stream'"
            ).fetchone()

            if not table_check or table_check[0] == 0:
                return total_metrics, store_metrics, recent_events

            # Overall metrics
            overall = con.execute("""
                SELECT
                    count(*) as total_events,
                    coalesce(sum(quantity * unit_price - discount_amount), 0.0) as total_revenue,
                    coalesce(avg(quantity * unit_price - discount_amount), 0.0) as avg_order_value
                FROM bronze.raw_sales_stream
            """).fetchone()

            if overall:
                total_metrics["total_events"] = overall[0]
                total_metrics["total_revenue"] = overall[1]
                total_metrics["avg_order_value"] = overall[2]

            # Store breakdown
            stores = con.execute("""
                SELECT
                    store_id,
                    store_name,
                    ship_city,
                    count(*) as events,
                    sum(quantity * unit_price - discount_amount) as revenue,
                    avg(quantity * unit_price - discount_amount) as aov,
                    max(created_at) as last_event
                FROM bronze.raw_sales_stream
                GROUP BY store_id, store_name, ship_city
                ORDER BY revenue DESC
            """).fetchall()

            for row in stores:
                store_metrics.append({
                    "store_id": row[0],
                    "store_name": row[1],
                    "city": row[2],
                    "events": row[3],
                    "revenue": row[4],
                    "aov": row[5],
                    "last_event": str(row[6]) if row[6] else "N/A",
                })

            # Recent events ticker
            recents = con.execute("""
                SELECT
                    event_id,
                    store_name,
                    pos_terminal_id,
                    order_id,
                    product_id,
                    quantity,
                    (quantity * unit_price - discount_amount) as net_amount,
                    channel,
                    payment_method,
                    created_at
                FROM bronze.raw_sales_stream
                ORDER BY created_at DESC
                LIMIT 8
            """).fetchall()

            for r in recents:
                recent_events.append({
                    "event_id": r[0],
                    "store_name": r[1],
                    "pos_terminal": r[2],
                    "order_id": r[3],
                    "product_id": r[4],
                    "quantity": r[5],
                    "net_amount": r[6],
                    "channel": r[7],
                    "payment_method": r[8],
                    "created_at": str(r[9]),
                })

        finally:
            con.close()
    except Exception as err:
        pass

    return total_metrics, store_metrics, recent_events


def render_dashboard(db_path: str) -> Layout:
    """Build Rich UI layout for live streaming sales dashboard."""
    totals, stores, recents = query_streaming_metrics(db_path)

    layout = Layout()
    layout.split(
        Layout(name="header", size=4),
        Layout(name="main", ratio=1),
    )
    layout["main"].split_row(
        Layout(name="stores", ratio=3),
        Layout(name="recents", ratio=4),
    )

    # Header Panel
    header_text = Text()
    header_text.append("⚡ MULTI-POS REAL-TIME SALES STREAM MONITOR ⚡\n", style="bold cyan")
    header_text.append(
        f"Total Streaming Events: {totals['total_events']:,} | "
        f"Gross Live Revenue: ${totals['total_revenue']:,.2f} | "
        f"Avg Transaction: ${totals['avg_order_value']:.2f} | "
        f"Refreshed: {datetime.now().strftime('%H:%M:%S')}",
        style="green bold",
    )
    layout["header"].update(Panel(header_text, style="blue", expand=True))

    # Stores Breakdown Table
    store_table = Table(title="POS Store Performance", expand=True, header_style="bold magenta")
    store_table.add_column("Store ID", style="cyan")
    store_table.add_column("Location Name", style="white")
    store_table.add_column("City", style="dim")
    store_table.add_column("Sales", justify="right", style="yellow")
    store_table.add_column("Revenue ($)", justify="right", style="green bold")
    store_table.add_column("AOV ($)", justify="right", style="blue")

    if not stores:
        store_table.add_row("-", "Waiting for POS events...", "-", "0", "$0.00", "$0.00")
    else:
        for s in stores:
            store_table.add_row(
                s["store_id"],
                s["store_name"],
                s["city"],
                f"{s['events']:,}",
                f"${s['revenue']:,.2f}",
                f"${s['aov']:.2f}",
            )

    layout["stores"].update(Panel(store_table, border_style="magenta"))

    # Recent Transactions Ticker Table
    recent_table = Table(title="Live Sales Stream Ticker", expand=True, header_style="bold green")
    recent_table.add_column("Time", style="dim")
    recent_table.add_column("Store", style="cyan")
    recent_table.add_column("POS Terminal", style="yellow")
    recent_table.add_column("Order ID", style="white")
    recent_table.add_column("Amount ($)", justify="right", style="green bold")
    recent_table.add_column("Payment", style="magenta")

    if not recents:
        recent_table.add_row("-", "No live transactions yet...", "-", "-", "$0.00", "-")
    else:
        for r in recents:
            time_str = r["created_at"].split("T")[-1][:8] if "T" in r["created_at"] else r["created_at"][-8:]
            recent_table.add_row(
                time_str,
                r["store_name"],
                r["pos_terminal"],
                r["order_id"],
                f"${r['net_amount']:,.2f}",
                r["payment_method"],
            )

    layout["recents"].update(Panel(recent_table, border_style="green"))

    return layout


def main(argv: list[str] | None = None) -> int:
    """Run interactive live monitoring dashboard."""
    args = parse_args(argv)

    start_time = time.time()
    try:
        with Live(render_dashboard(args.duckdb_path), refresh_per_second=1.0 / max(args.refresh_rate, 0.2)) as live:
            while True:
                elapsed = time.time() - start_time
                if args.duration > 0 and elapsed >= args.duration:
                    break
                time.sleep(args.refresh_rate)
                live.update(render_dashboard(args.duckdb_path))
    except KeyboardInterrupt:
        console.print("[yellow]Monitor stopped by user.[/yellow]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
