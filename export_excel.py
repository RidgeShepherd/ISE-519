"""Export the saved Shopify test orders into a standalone Excel workbook."""

from collections import defaultdict
from contextlib import closing
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import sqlite3
from tempfile import NamedTemporaryFile

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.table import Table, TableStyleInfo

PROJECT = Path(__file__).resolve().parent
DATABASE = PROJECT / "bbq_demo.sqlite3"
OUTPUT = PROJECT / "BBQ_Shopify_Demo.xlsx"


# Number of (Slobberin Sauce, Dr. D's Sauce) bottles per SKU unit.
BOTTLES_PER_SKU = {
    "SAUCE-001": (0, 1),
    "SAUCE-002": (0, 2),
    "SAUCE-003": (1, 1),
    "SAUCE-004": (1, 0),
    "SAUCE-005": (2, 0),
}


def count_bottles(lines):
    ss = dd = 0
    unmapped = set()
    for sku, quantity in lines:
        bottles = BOTTLES_PER_SKU.get(sku)
        if bottles is None:
            unmapped.add(sku or "(no SKU)")
            continue
        ss += bottles[0] * quantity
        dd += bottles[1] * quantity
    return ss, dd, unmapped


def add_table(sheet, name, ref):
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showRowStripes=True
    )
    sheet.add_table(table)


def main():
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
        db.execute("BEGIN")
        has_amounts = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='order_amounts'"
        ).fetchone()
        amount_columns = (
            "a.item_cents, a.shipping_cents, a.tax_cents"
            if has_amounts else "NULL, NULL, NULL"
        )
        amount_join = (
            "LEFT JOIN order_amounts AS a ON a.order_id = o.shopify_id"
            if has_amounts else ""
        )
        orders = db.execute(f"""
            SELECT o.order_number, o.currency, {amount_columns}, o.total_cents
            FROM orders AS o {amount_join}
            ORDER BY o.order_number, o.shopify_id
        """).fetchall()
        order_columns = {column[1] for column in db.execute("PRAGMA table_info(orders)")}
        date_column = "created_at" if "created_at" in order_columns else "NULL"
        dates = dict(db.execute(f"SELECT order_number, {date_column} FROM orders"))
        items = db.execute("""
            SELECT o.order_number, i.sku, i.quantity
            FROM order_items AS i
            JOIN orders AS o ON o.shopify_id = i.order_id
            ORDER BY o.order_number, i.sku, i.shopify_id
        """).fetchall()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Shopify Import"
    sheet["A1"] = "Shopify test orders"
    sheet["H1"] = "Shopify test order items"
    sheet["A2"] = "Blank amounts require a fresh Shopify sync."
    for cell in ("A1", "H1"):
        sheet[cell].font = Font(bold=True, size=14)

    for start_column, headers, rows, name in (
        (1, ("Order", "Currency", "Item Charge", "Shipping Revenue", "Shopify Tax", "Order total"),
         [(number, currency, *(c / 100 if c is not None else None for c in amounts))
          for number, currency, *amounts in orders],
         "ShopifyOrders"),
        (8, ("Order", "SKU", "SKU quantity"), items, "ShopifyOrderItems"),
    ):
        for row_number, row in enumerate([headers, *rows], start=4):
            for column, value in enumerate(row, start=start_column):
                cell = sheet.cell(row_number, column, value)
                if row_number > 4 and isinstance(value, str):
                    cell.data_type = "s"
        if rows:
            first, last = ("A", "F") if start_column == 1 else ("H", "J")
            add_table(sheet, name, f"{first}4:{last}{4 + len(rows)}")

    for row in range(5, 5 + len(orders)):
        for column in "CDEF":
            sheet[f"{column}{row}"].number_format = '"$"#,##0.00'
    for column, width in zip("ABCDEFGHIJ", (16, 12, 16, 21, 16, 16, 4, 16, 18, 16)):
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = "A5"

    preview = workbook.create_sheet("Sales Preview")
    preview.append([
        "Date", "Invoice", "Item Charge", "Shipping Revenue", "Shopify Tax",
        None, None, None, "Total", None, None, None, "Mixed Sale", "SS", "DD",
    ])
    preview.row_dimensions[1].height = 34
    for cell in preview[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    preview["E1"].comment = Comment(
        "This preview shows total tax reported by Shopify, without a state or county breakdown.",
        "Shopify export",
    )
    items_by_order = defaultdict(list)
    for invoice, sku, quantity in items:
        items_by_order[invoice].append((sku, quantity))
    eastern = ZoneInfo("America/New_York")
    for number, _, item, shipping, tax, _ in orders:
        timestamp = dates[number]
        date = (
            datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(eastern).date()
            if timestamp else None
        )
        preview.append([
            date, number, *(cents / 100 if cents is not None else None
                            for cents in (item, shipping, tax)),
            None, None, None,
        ])
        row = preview.max_row
        lines = items_by_order[number]
        ss, dd, unmapped = count_bottles(lines)
        if ss > 0 and dd > 0:
            preview[f"M{row}"] = "SS/DD"
        if unmapped:
            preview[f"N{row}"].comment = Comment(
                "Bottle counts unavailable for unmapped SKU(s): "
                + ", ".join(sorted(unmapped)),
                "Shopify export",
            )
        elif lines:
            preview[f"N{row}"] = ss
            preview[f"O{row}"] = dd
        preview[f"I{row}"] = f'=IF(COUNT(C{row}:E{row})=3,SUM(C{row}:E{row}),"")'
        preview[f"B{row}"].data_type = "s"
        preview[f"A{row}"].number_format = "yyyy-mm-dd"
        for column in "CDEFGHIJK":
            preview[f"{column}{row}"].number_format = '"$"#,##0.00'
    widths = (15, 15, 16, 21, 26, 16, 20, 20, 21, 22, 23, 4, 16, 12, 12, 15, 16)
    for column, width in zip("ABCDEFGHIJKLMNOPQ", widths):
        preview.column_dimensions[column].width = width
    preview.freeze_panes = "C2"

    # Finish writing the new copy before replacing the previous export.
    with NamedTemporaryFile(dir=PROJECT, suffix=".xlsx", delete=False) as file:
        temporary = Path(file.name)
    try:
        workbook.save(temporary)
        temporary.replace(OUTPUT)
    finally:
        temporary.unlink(missing_ok=True)
        workbook.close()

    print(f"Exported {len(orders)} orders and {len(items)} line items.")
    print(OUTPUT)


if __name__ == "__main__":
    main()
