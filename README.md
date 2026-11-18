# ISE 519 Shopify Sales Prototype

This prototype pulls Shopify test orders into SQLite and exports an Excel sales preview with one row per invoice. It demonstrates how Dr. D could reduce manual order entry into his workbook.

## Run the offline demo

Requirements are Python 3.10 or later, the SQLite command-line tool, and a shell such as macOS Terminal. Run these commands from the repository root in a fresh checkout.

```sh
sqlite3 -bail bbq_demo.sqlite3 < sql/demo_dump.sql
sqlite3 -bail -header -column -readonly bbq_demo.sqlite3 < sql/queries.sql
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python export_excel.py
```

Open `BBQ_Shopify_Demo.xlsx` and select **Sales Preview**. The dump restores **10 orders, 16 line items, 21 SKU units, and $313.00** in order totals. SKU units count packs as purchased. The Excel preview converts packs to individual bottle counts using the SKU mapping in `export_excel.py`.

| Invoice | Shopify order total | Shipping | Mixed Sale | SS bottles | DD bottles |
|---|---:|---:|---|---:|---:|
| #1009 | $33.00 | $5.00 | SS/DD | 2 | 1 |
| #1010 | $38.00 | $8.00 | SS/DD | 1 | 2 |

Invoice #1004 has a custom line without a SKU. Its bottle-count cells are blank and the preview includes a note.

## Relational schema and queries

- `orders` has one row per order, keyed by Shopify order ID.
- `order_items` has one row per line item, keyed by Shopify line-item ID. Its `order_id` foreign key links many items to one order.
- `order_amounts` uses the order ID as both its primary and foreign key. This stores at most one subtotal, shipping and tax breakdown per order.
- `sql/schema.sql` creates a blank schema. `sql/demo_dump.sql` creates and populates the schema in one step.
- `sql/queries.sql` traces two invoices to their SKUs and aggregates line-item counts and shipping at invoice level. The Excel exporter calculates sauce bottle counts and the mixed-sale flag.

## Data and live Shopify sync

The packaged data came from test transactions in the class development store. The dump retains test invoice numbers, timestamps, SKUs, quantities, and monetary fields and substitutes demo identifiers for Shopify record IDs. Dr. D’s draft workbook and its records are excluded from the public demo. The standalone export reproduces the fields used in the project’s sales preview.

To try live ingestion, use a **separate fresh checkout** and skip the offline dump restore. Set these variables for your own development store and app with order read access.

```sh
export SHOPIFY_STORE_URL="https://your-store.myshopify.com"
export SHOPIFY_CLIENT_ID="your-app-client-id"
python3 sync_orders.py
```

Enter the app secret at the hidden terminal prompt. The sync requests test orders only, accepts USD, and stops before importing any rows if the response requires more than one page of orders or line items. It updates existing orders by Shopify ID and replaces their line items within the same transaction. Run the SQL and Excel commands from the offline demo against the resulting database.
