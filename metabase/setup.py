#!/usr/bin/env python3
"""
Metabase Automated Setup Script.

Configures Metabase via REST API after container startup:
1. Waits for Metabase to be healthy
2. Creates admin user (if first-time setup)
3. Sets up DuckDB database connection
4. Creates 3 dashboards with cards

Usage:
    python metabase/setup.py [--base-url URL] [--username USER] [--password PASS]
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger("metabase_setup")

# ── Defaults ──
DEFAULT_BASE_URL = "http://localhost:3000"
DEFAULT_USERNAME = "admin@example.com"
DEFAULT_PASSWORD = "password"
DASHBOARD_DIR = Path(__file__).parent / "dashboards"

# ── DuckDB connection details ──
DUCKDB_CONNECTION = {
    "engine": "duckdb",
    "name": "Sales Analytics Warehouse",
    "details": {
        "db": "/data/warehouse/sales_analytics.duckdb",
    },
}


def api_request(method, url, session_id=None, data=None):
    """Make an HTTP request to the Metabase API."""
    headers = {"Content-Type": "application/json"}
    if session_id:
        headers["X-Metabase-Session"] = session_id
    req = Request(url, method=method, headers=headers)
    if data is not None:
        req.data = json.dumps(data).encode()
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.code != 204 else ""
        logger.error("HTTP %d: %s", e.code, body)
        return None


def wait_for_metabase(base_url, timeout=120):
    """Wait for Metabase to become healthy."""
    logger.info("Waiting for Metabase at %s ...", base_url)
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = api_request("GET", f"{base_url}/api/health")
            if resp and resp.get("status") == "ok":
                logger.info("Metabase is healthy.")
                return True
        except Exception:
            pass
        time.sleep(5)
    logger.error("Timeout waiting for Metabase to become healthy.")
    return False


def setup_admin(base_url, username, password):
    """Create admin user via setup API (first-time setup)."""
    logger.info("Checking if setup is needed...")
    resp = api_request("GET", f"{base_url}/api/session/properties")
    if resp is None:
        return None
    if resp.get("setup-token"):
        token = resp["setup-token"]
        logger.info("First-time setup with token: %s", token)
        setup_data = {
            "token": token,
            "user": {
                "first_name": "Admin",
                "last_name": "User",
                "email": username,
                "password": password,
                "site_name": "Sales Analytics",
            },
            "prefs": {
                "allow_tracking": False,
                "site_name": "Sales Analytics",
            },
            "database": None,
        }
        resp = api_request("POST", f"{base_url}/api/setup", data=setup_data)
        if resp:
            logger.info("Admin user created.")
            return resp.get("id")
        return None
    else:
        # Already set up — log in
        logger.info("Metabase already configured — logging in.")
        login_data = {"username": username, "password": password}
        resp = api_request("POST", f"{base_url}/api/session", data=login_data)
        if resp:
            logger.info("Logged in as %s", username)
            return resp.get("id")
        return None


def add_database_connection(base_url, session_id):
    """Add DuckDB database connection."""
    logger.info("Adding DuckDB database connection...")
    # Check if database already exists
    databases = api_request("GET", f"{base_url}/api/database", session_id)
    if databases:
        for db in databases.get("data", []):
            if db.get("name") == DUCKDB_CONNECTION["name"]:
                logger.info("Database '%s' already exists — skipping.", db["name"])
                return db["id"]
    resp = api_request(
        "POST",
        f"{base_url}/api/database",
        session_id,
        data=DUCKDB_CONNECTION,
    )
    if resp:
        logger.info("Database connection created: id=%s", resp.get("id"))
        return resp.get("id")
    return None


def sync_database(base_url, session_id, db_id):
    """Trigger schema sync for a database."""
    logger.info("Syncing database schema...")
    resp = api_request(
        "POST",
        f"{base_url}/api/database/{db_id}/sync",
        session_id,
    )
    if resp is not None or True:  # 204 No Content is success
        logger.info("Sync triggered for database %s.", db_id)
        # Wait a bit for sync to complete
        time.sleep(10)
        return True
    return False


def create_dashboard(base_url, session_id, name, description=None):
    """Create a new dashboard."""
    logger.info("Creating dashboard: %s", name)
    data = {"name": name}
    if description:
        data["description"] = description
    resp = api_request("POST", f"{base_url}/api/dashboard", session_id, data=data)
    if resp:
        logger.info("Dashboard created: id=%s name=%s", resp.get("id"), resp.get("name"))
        return resp.get("id")
    return None


def add_card_to_dashboard(base_url, session_id, dashboard_id, card_data):
    """Add a card (question) to a dashboard."""
    logger.info("Adding card '%s' to dashboard %s", card_data.get("name", ""), dashboard_id)
    # First create the card/question
    question_data = {
        "name": card_data["name"],
        "display": card_data.get("display", "table"),
        "dataset_query": {
            "database": card_data.get("database_id"),
            "type": "query",
            "query": card_data.get("query", {}),
        },
        "visualization_settings": card_data.get("visualization_settings", {}),
    }
    card_resp = api_request(
        "POST",
        f"{base_url}/api/card",
        session_id,
        data=question_data,
    )
    if not card_resp:
        logger.error("Failed to create card: %s", card_data["name"])
        return None
    card_id = card_resp.get("id")
    logger.info("Card created: id=%s name=%s", card_id, card_resp.get("name"))
    # Add card to dashboard
    dashcard_data = {
        "cardId": card_id,
        "row": card_data.get("row", 0),
        "col": card_data.get("col", 0),
        "size_x": card_data.get("size_x", 4),
        "size_y": card_data.get("size_y", 4),
    }
    resp = api_request(
        "POST",
        f"{base_url}/api/dashboard/{dashboard_id}/cards",
        session_id,
        data=dashcard_data,
    )
    if resp:
        logger.info("Card added to dashboard.")
    return card_id


def main():
    parser = argparse.ArgumentParser(description="Setup Metabase automatically")
    parser.add_argument("--base-url", default=os.environ.get("MB_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--username", default=os.environ.get("MB_USER", DEFAULT_USERNAME))
    parser.add_argument("--password", default=os.environ.get("MB_PASS", DEFAULT_PASSWORD))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not wait_for_metabase(args.base_url):
        sys.exit(1)

    session_id = setup_admin(args.base_url, args.username, args.password)
    if not session_id:
        logger.error("Failed to set up admin / log in.")
        sys.exit(1)

    db_id = add_database_connection(args.base_url, session_id)
    if not db_id:
        logger.error("Failed to add database connection.")
        sys.exit(1)

    sync_database(args.base_url, session_id, db_id)

    # Load dashboard definitions and create them
    if DASHBOARD_DIR.exists():
        for dash_file in sorted(DASHBOARD_DIR.glob("*.json")):
            with open(dash_file) as f:
                dashboard_def = json.load(f)

            dash_id = create_dashboard(
                args.base_url, session_id,
                dashboard_def["name"],
                dashboard_def.get("description"),
            )
            if not dash_id:
                logger.warning("Skipping dashboard: %s", dashboard_def["name"])
                continue

            for card in dashboard_def.get("cards", []):
                card["database_id"] = db_id
                add_card_to_dashboard(args.base_url, session_id, dash_id, card)
                time.sleep(1)  # Rate limiting

            logger.info("Dashboard '%s' completed.", dashboard_def["name"])

    logger.info("Metabase setup complete!")

    # Print connection info
    logger.info("=" * 50)
    logger.info("Metabase is ready at %s", args.base_url)
    logger.info("Login: %s / %s", args.username, args.password)
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
