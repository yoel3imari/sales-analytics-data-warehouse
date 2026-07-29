#!/usr/bin/env python3
"""
Metabase Automated Setup Script.

Configures Metabase via REST API after container startup:
1. Waits for Metabase to be healthy
2. Creates admin user (if first-time setup)
3. Sets up DuckDB database connection
4. Creates 3 dashboards with cards, filters, and parameter mappings

Usage:
    python metabase/setup.py [--base-url URL] [--username USER] [--password PASS]
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger("metabase_setup")

DEFAULT_BASE_URL = "http://localhost:3000"
DEFAULT_USERNAME = "admin@example.com"
DEFAULT_PASSWORD = "SalesAnalytics2026!"
DASHBOARD_DIR = Path(__file__).parent / "dashboards"

DUCKDB_CONNECTION = {
    "engine": "duckdb",
    "name": "Sales Analytics Warehouse",
    "details": {
        "database_file": "/data/warehouse/sales_analytics.duckdb",
        "read_only": True,
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
        logger.info("Setup endpoint did not return session, attempting login...")

    logger.info("Logging into Metabase...")
    login_data = {"username": username, "password": password}
    resp = api_request("POST", f"{base_url}/api/session", data=login_data)
    if resp:
        logger.info("Logged in as %s", username)
        return resp.get("id")
    return None


def add_database_connection(base_url, session_id):
    """Add DuckDB database connection."""
    logger.info("Adding DuckDB database connection...")
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
    logger.info("Syncing database schema...")
    resp = api_request(
        "POST",
        f"{base_url}/api/database/{db_id}/sync",
        session_id,
    )
    if resp is not None or True:
        logger.info("Sync triggered for database %s.", db_id)
        time.sleep(10)
        return True
    return False


def create_dashboard(base_url, session_id, name, description=None, parameters=None):
    """Create a new dashboard with optional filter parameters."""
    logger.info("Creating dashboard: %s", name)
    data = {"name": name}
    if description:
        data["description"] = description
    if parameters:
        data["parameters"] = parameters
    resp = api_request("POST", f"{base_url}/api/dashboard", session_id, data=data)
    if resp:
        logger.info("Dashboard created: id=%s name=%s", resp.get("id"), resp.get("name"))
        return resp.get("id")
    return None


def create_card(base_url, session_id, card_data):
    """Create a card (question) — supports native SQL, GUI, and text cards."""
    logger.info("Creating card '%s'", card_data.get("name", ""))

    question_data = {
        "name": card_data["name"],
        "display": card_data.get("display", "table"),
        "visualization_settings": card_data.get("visualization_settings", {}),
    }

    if card_data.get("display") == "text":
        question_data["dataset_query"] = {
            "type": "native",
            "native": {"query": "SELECT 1"},
            "database": card_data.get("database_id"),
        }
        if "text_content" in card_data:
            question_data["visualization_settings"]["text"] = card_data["text_content"]
    elif "native_query" in card_data:
        dataset_query = {
            "database": card_data.get("database_id"),
            "type": "native",
            "native": {"query": card_data["native_query"]},
        }
        template_tags = card_data.get("template_tags")
        if template_tags:
            tags_with_ids = {}
            for tag_name, tag_def in template_tags.items():
                tag_def = dict(tag_def)
                tag_def["id"] = str(uuid.uuid4())
                tags_with_ids[tag_name] = tag_def
            dataset_query["native"]["template-tags"] = tags_with_ids
        question_data["dataset_query"] = dataset_query
    else:
        question_data["dataset_query"] = {
            "database": card_data.get("database_id"),
            "type": "query",
            "query": card_data.get("query", {}),
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
    return card_id


def attach_cards_to_dashboard(base_url, session_id, dashboard_id, cards):
    """Attach multiple cards to a dashboard with positions and parameter mappings."""
    logger.info("Attaching %d cards to dashboard %s", len(cards), dashboard_id)
    cards_payload = []
    for idx, card in enumerate(cards, start=1):
        entry = {
            "id": -idx,
            "card_id": card["card_id"],
            "row": card.get("row", 0),
            "col": card.get("col", 0),
            "size_x": card.get("size_x", 4),
            "size_y": card.get("size_y", 4),
        }
        mappings = card.get("parameter_mappings")
        if mappings:
            entry["parameter_mappings"] = [
                {**m, "card_id": card["card_id"]} for m in mappings
            ]
        cards_payload.append(entry)

    resp = api_request(
        "PUT",
        f"{base_url}/api/dashboard/{dashboard_id}/cards",
        session_id,
        data={"cards": cards_payload},
    )
    if resp is not None:
        logger.info("All cards attached to dashboard %s.", dashboard_id)
    return resp


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
        logger.error(
            "Failed to add DuckDB database connection. "
            "Make sure the data pipeline has been run:\n"
            "    ./start.sh generate && ./start.sh build"
        )
        sys.exit(1)

    sync_database(args.base_url, session_id, db_id)

    if DASHBOARD_DIR.exists():
        for dash_file in sorted(DASHBOARD_DIR.glob("*.json")):
            with open(dash_file) as f:
                dashboard_def = json.load(f)

            dash_id = create_dashboard(
                args.base_url, session_id,
                dashboard_def["name"],
                dashboard_def.get("description"),
                dashboard_def.get("parameters"),
            )
            if not dash_id:
                logger.warning("Skipping dashboard: %s", dashboard_def["name"])
                continue

            dash_cards = []
            for card in dashboard_def.get("cards", []):
                card["database_id"] = db_id
                card_id = create_card(args.base_url, session_id, card)
                if card_id:
                    card["card_id"] = card_id
                    dash_cards.append(card)
                time.sleep(0.5)

            if dash_cards:
                attach_cards_to_dashboard(
                    args.base_url, session_id, dash_id, dash_cards
                )

            logger.info("Dashboard '%s' completed.", dashboard_def["name"])

    logger.info("Metabase setup complete!")
    logger.info("=" * 50)
    logger.info("Metabase is ready at %s", args.base_url)
    logger.info("Login: %s / %s", args.username, args.password)
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
