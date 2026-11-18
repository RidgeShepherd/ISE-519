PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;
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

INSERT INTO "orders" VALUES('demo-order-01','#1001',1000,'USD','2026-11-18T15:53:52Z');
INSERT INTO "orders" VALUES('demo-order-02','#1002',3000,'USD','2026-11-18T15:56:06Z');
INSERT INTO "orders" VALUES('demo-order-03','#1003',3600,'USD','2026-11-18T15:56:44Z');
INSERT INTO "orders" VALUES('demo-order-04','#1004',1500,'USD','2026-11-18T17:23:43Z');
INSERT INTO "orders" VALUES('demo-order-05','#1005',1500,'USD','2026-11-18T17:58:32Z');
INSERT INTO "orders" VALUES('demo-order-06','#1006',3600,'USD','2026-11-18T18:03:39Z');
INSERT INTO "orders" VALUES('demo-order-07','#1007',4600,'USD','2026-11-18T18:04:16Z');
INSERT INTO "orders" VALUES('demo-order-08','#1008',5400,'USD','2026-11-18T18:05:49Z');
INSERT INTO "orders" VALUES('demo-order-09','#1009',3300,'USD','2026-11-18T18:14:24Z');
INSERT INTO "orders" VALUES('demo-order-10','#1010',3800,'USD','2026-11-18T18:14:40Z');
INSERT INTO "order_amounts" VALUES('demo-order-01',1000,0,0);
INSERT INTO "order_amounts" VALUES('demo-order-02',3000,0,0);
INSERT INTO "order_amounts" VALUES('demo-order-03',3600,0,0);
INSERT INTO "order_amounts" VALUES('demo-order-04',1000,500,0);
INSERT INTO "order_amounts" VALUES('demo-order-05',1000,500,0);
INSERT INTO "order_amounts" VALUES('demo-order-06',3600,0,0);
INSERT INTO "order_amounts" VALUES('demo-order-07',4600,0,0);
INSERT INTO "order_amounts" VALUES('demo-order-08',5400,0,0);
INSERT INTO "order_amounts" VALUES('demo-order-09',2800,500,0);
INSERT INTO "order_amounts" VALUES('demo-order-10',3000,800,0);
INSERT INTO "order_items" VALUES('demo-order-01-line-1','demo-order-01','SAUCE-001',1);
INSERT INTO "order_items" VALUES('demo-order-02-line-1','demo-order-02','SAUCE-004',3);
INSERT INTO "order_items" VALUES('demo-order-03-line-1','demo-order-03','SAUCE-002',1);
INSERT INTO "order_items" VALUES('demo-order-03-line-2','demo-order-03','SAUCE-003',1);
INSERT INTO "order_items" VALUES('demo-order-04-line-1','demo-order-04',NULL,1);
INSERT INTO "order_items" VALUES('demo-order-05-line-1','demo-order-05','SAUCE-001',1);
INSERT INTO "order_items" VALUES('demo-order-06-line-1','demo-order-06','SAUCE-002',1);
INSERT INTO "order_items" VALUES('demo-order-06-line-2','demo-order-06','SAUCE-005',1);
INSERT INTO "order_items" VALUES('demo-order-07-line-1','demo-order-07','SAUCE-003',2);
INSERT INTO "order_items" VALUES('demo-order-07-line-2','demo-order-07','SAUCE-004',1);
INSERT INTO "order_items" VALUES('demo-order-08-line-1','demo-order-08','SAUCE-002',2);
INSERT INTO "order_items" VALUES('demo-order-08-line-2','demo-order-08','SAUCE-003',1);
INSERT INTO "order_items" VALUES('demo-order-09-line-1','demo-order-09','SAUCE-001',1);
INSERT INTO "order_items" VALUES('demo-order-09-line-2','demo-order-09','SAUCE-005',1);
INSERT INTO "order_items" VALUES('demo-order-10-line-1','demo-order-10','SAUCE-001',2);
INSERT INTO "order_items" VALUES('demo-order-10-line-2','demo-order-10','SAUCE-004',1);
COMMIT;
