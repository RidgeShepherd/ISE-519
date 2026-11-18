import json
import os
import re
import sqlite3
from contextlib import closing
from decimal import Decimal
from getpass import getpass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


STORE_URL = os.environ.get("SHOPIFY_STORE_URL", "").rstrip("/")
CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "")
API_VERSION = "2026-10"
DB_PATH = Path(__file__).resolve().with_name("bbq_demo.sqlite3")

ORDERS_QUERY = """
{
  orders(first: 10, query: "test:true") {
    pageInfo { hasNextPage }
    nodes {
      id
      name
      createdAt
      currentSubtotalPriceSet { shopMoney { amount currencyCode } }
      currentShippingPriceSet { shopMoney { amount currencyCode } }
      currentTotalTaxSet { shopMoney { amount currencyCode } }
      currentTotalPriceSet { shopMoney { amount currencyCode } }
      lineItems(first: 20) {
        pageInfo { hasNextPage }
        nodes { id sku quantity }
      }
    }
  }
}
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    shopify_id TEXT PRIMARY KEY NOT NULL,
    order_number TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    currency TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    shopify_id TEXT PRIMARY KEY NOT NULL,
    order_id TEXT NOT NULL REFERENCES orders(shopify_id),
    sku TEXT,
    quantity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS order_amounts (
    order_id TEXT PRIMARY KEY NOT NULL REFERENCES orders(shopify_id),
    item_cents INTEGER NOT NULL,
    shipping_cents INTEGER NOT NULL,
    tax_cents INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS order_items_order_id_idx
    ON order_items(order_id);
"""


def post(path, body, headers):
    request = Request(STORE_URL + path, data=body, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        raise SystemExit(f"Shopify returned HTTP {error.code} at {path}.")
    except (URLError, TimeoutError):
        raise SystemExit(f"Could not connect to Shopify at {path}.")


def main():
    if not re.fullmatch(r"https://[a-z0-9][a-z0-9-]*\.myshopify\.com", STORE_URL):
        raise SystemExit("Set SHOPIFY_STORE_URL to your HTTPS myshopify.com store URL.")
    if not CLIENT_ID:
        raise SystemExit("Set SHOPIFY_CLIENT_ID to your development app client ID.")
    client_secret = getpass("Shopify Client secret: ").strip()
    if not client_secret:
        raise SystemExit("No client secret was entered.")

    token_response = post(
        "/admin/oauth/access_token",
        urlencode({
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": client_secret,
        }).encode(),
        {"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = token_response["access_token"]

    result = post(
        f"/admin/api/{API_VERSION}/graphql.json",
        json.dumps({"query": ORDERS_QUERY}).encode(),
        {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": token,
        },
    )
    if result.get("errors"):
        raise SystemExit("\n".join(error["message"] for error in result["errors"]))

    order_page = result["data"]["orders"]
    orders = order_page["nodes"]
    if order_page["pageInfo"]["hasNextPage"] or any(
        order["lineItems"]["pageInfo"]["hasNextPage"] for order in orders
    ):
        raise SystemExit("More Shopify pages are available. No rows were written.")

    with closing(sqlite3.connect(DB_PATH)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(SCHEMA)

        # Commit the full import together, or roll it back if a row fails.
        with db:
            db.execute("BEGIN IMMEDIATE")
            columns = {column[1] for column in db.execute("PRAGMA table_info(orders)")}
            if "created_at" not in columns:
                db.execute("ALTER TABLE orders ADD COLUMN created_at TEXT")
            for order in orders:
                money = order["currentTotalPriceSet"]["shopMoney"]
                if money["currencyCode"] != "USD":
                    raise ValueError(f'{order["name"]} is not a USD order.')
                total_cents = int(Decimal(money["amount"]) * 100)

                db.execute("""
                    INSERT INTO orders (
                        shopify_id, order_number, total_cents, currency, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(shopify_id) DO UPDATE SET
                        order_number = excluded.order_number,
                        total_cents = excluded.total_cents,
                        currency = excluded.currency,
                        created_at = excluded.created_at
                """, (order["id"], order["name"], total_cents, money["currencyCode"], order["createdAt"]))

                amounts = [
                    order[field]["shopMoney"]
                    for field in (
                        "currentSubtotalPriceSet", "currentShippingPriceSet",
                        "currentTotalTaxSet",
                    )
                ]
                if any(amount["currencyCode"] != "USD" for amount in amounts):
                    raise ValueError("Order amounts must use USD.")
                db.execute("""
                    INSERT INTO order_amounts VALUES (?, ?, ?, ?)
                    ON CONFLICT(order_id) DO UPDATE SET
                        item_cents = excluded.item_cents,
                        shipping_cents = excluded.shipping_cents,
                        tax_cents = excluded.tax_cents
                """, (order["id"], *(
                    int(Decimal(amount["amount"]) * 100) for amount in amounts
                )))

                # Replace this order's line items with Shopify's current list.
                db.execute(
                    "DELETE FROM order_items WHERE order_id = ?",
                    (order["id"],),
                )
                db.executemany("""
                    INSERT INTO order_items (shopify_id, order_id, sku, quantity)
                    VALUES (?, ?, ?, ?)
                """, [
                    (item["id"], order["id"], item["sku"], item["quantity"])
                    for item in order["lineItems"]["nodes"]
                ])

        order_count, total_cents = db.execute("""
            SELECT COUNT(*), COALESCE(SUM(total_cents), 0) FROM orders
        """).fetchone()
        line_count, units = db.execute("""
            SELECT COUNT(*), COALESCE(SUM(quantity), 0) FROM order_items
        """).fetchone()

    print(f"Database: {DB_PATH}")
    print(
        f"SQLite: {order_count} orders | {line_count} line items | "
        f"{units} SKU units | ${Decimal(total_cents) / 100:.2f}"
    )


if __name__ == "__main__":
    main()