-- Trace the two shipped demo invoices to their product lines.
SELECT o.order_number AS invoice, i.sku, i.quantity
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.shopify_id
WHERE o.order_number IN ('#1009', '#1010')
ORDER BY invoice, i.sku;

-- One row per invoice. Aggregate line items before joining order amounts.
WITH item_counts AS (
    SELECT order_id, COUNT(*) AS line_count, SUM(quantity) AS sku_units
    FROM order_items
    GROUP BY order_id
)
SELECT o.order_number AS invoice,
       COALESCE(i.line_count, 0) AS line_count,
       COALESCE(i.sku_units, 0) AS sku_units,
       a.shipping_cents / 100.0 AS shipping_usd,
       o.total_cents / 100.0 AS total_usd
FROM orders AS o
LEFT JOIN order_amounts AS a ON a.order_id = o.shopify_id
LEFT JOIN item_counts AS i ON i.order_id = o.shopify_id
ORDER BY invoice;
