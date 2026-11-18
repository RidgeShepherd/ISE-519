PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS orders (
    shopify_id TEXT PRIMARY KEY NOT NULL,
    order_number TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    currency TEXT NOT NULL,
    created_at TEXT
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
