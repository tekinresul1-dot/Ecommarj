import sqlite3
import sys
from datetime import datetime, time
from zoneinfo import ZoneInfo
from decimal import Decimal

ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")

def parse_istanbul_date_range(min_date_str, max_date_str):
    if not (min_date_str and max_date_str):
        return None, None
    min_date = datetime.strptime(min_date_str, "%Y-%m-%d").replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=ISTANBUL_TZ
    )
    max_date = datetime.combine(
        datetime.strptime(max_date_str, "%Y-%m-%d").date(),
        time.max,
        tzinfo=ISTANBUL_TZ,
    )
    return min_date, max_date

def calculate_toplam_ciro(min_date_str, max_date_str):
    min_date, max_date = parse_istanbul_date_range(min_date_str, max_date_str)
    
    # Connect to local SQLite database
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    
    # We need to filter orders where:
    # (last_modified_date >= min_date AND last_modified_date <= max_date) OR
    # (last_modified_date IS NULL AND order_date >= min_date AND order_date <= max_date)
    #
    # Wait, SQLite dates are stored as ISO 8601 strings (e.g. '2026-05-23T22:30:00+03:00' or in UTC).
    # Let's see how they are formatted in the database.
    # Let's query one row to check formatting first.
    cursor.execute("SELECT order_date, last_modified_date, status, id FROM core_order LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("No orders in database!")
        return
    
    # Fetch all orders that fall in the date range.
    # Since SQLite doesn't natively parse timezone offsets perfectly for all operators,
    # let's fetch orders and filter them in Python using datetime parsing!
    cursor.execute("""
        SELECT id, order_date, last_modified_date, status, channel
        FROM core_order
    """)
    all_orders = cursor.fetchall()
    
    DASHBOARD_REVENUE_STATUSES = {"Delivered", "Shipped"}
    RETURN_STATUSES = {"Returned", "UnDelivered"}
    CANCEL_STATUSES = {"Cancelled", "UnSupplied"}
    GROSS_SALES_STATUSES = DASHBOARD_REVENUE_STATUSES | RETURN_STATUSES | CANCEL_STATUSES
    
    def parse_db_datetime(dt_str):
        if not dt_str:
            return None
        # Handle trailing Z or offsets
        # Django stores aware datetimes in SQLite as strings: e.g. "2026-05-23 19:30:00" in UTC
        # or with offset. Let's try multiple formats.
        dt_str = dt_str.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                dt = datetime.strptime(dt_str, fmt)
                if dt.tzinfo is None:
                    # Django default is UTC when USE_TZ=True and engine is SQLite
                    dt = dt.replace(tzinfo=ZoneInfo("UTC"))
                return dt.astimezone(ISTANBUL_TZ)
            except ValueError:
                continue
        raise ValueError(f"Could not parse datetime: {dt_str}")

    included_order_ids = []
    cancelled_order_ids = []
    returned_order_ids = []
    gross_sales_order_ids = []
    
    for order_id, order_date_str, last_modified_date_str, status, channel in all_orders:
        order_date = parse_db_datetime(order_date_str)
        last_modified = parse_db_datetime(last_modified_date_str)
        
        effective_date = last_modified if last_modified is not None else order_date
        
        if min_date <= effective_date <= max_date:
            if status in DASHBOARD_REVENUE_STATUSES:
                included_order_ids.append(order_id)
            if status in CANCEL_STATUSES:
                cancelled_order_ids.append(order_id)
            if status in RETURN_STATUSES:
                returned_order_ids.append(order_id)
            if status in GROSS_SALES_STATUSES:
                gross_sales_order_ids.append(order_id)

    # 1. total_gross and total_discount from gross sales order items
    if not gross_sales_order_ids:
        total_gross = Decimal("0.00")
        total_discount = Decimal("0.00")
    else:
        placeholders = ",".join("?" for _ in gross_sales_order_ids)
        cursor.execute(f"""
            SELECT SUM(sale_price_gross), SUM(discount)
            FROM core_orderitem
            WHERE order_id IN ({placeholders})
        """, gross_sales_order_ids)
        g_row = cursor.fetchone()
        total_gross = Decimal(str(g_row[0] or "0.00"))
        total_discount = Decimal(str(g_row[1] or "0.00"))

    # 2. cancelled_total from cancelled order items
    if not cancelled_order_ids:
        cancelled_total = Decimal("0.00")
    else:
        placeholders = ",".join("?" for _ in cancelled_order_ids)
        cursor.execute(f"""
            SELECT SUM(sale_price_net)
            FROM core_orderitem
            WHERE order_id IN ({placeholders})
        """, cancelled_order_ids)
        cancelled_total = Decimal(str(cursor.fetchone()[0] or "0.00"))

    # 3. returned_status_total from returned order items
    if not returned_order_ids:
        returned_status_total = Decimal("0.00")
    else:
        placeholders = ",".join("?" for _ in returned_order_ids)
        cursor.execute(f"""
            SELECT SUM(sale_price_net)
            FROM core_orderitem
            WHERE order_id IN ({placeholders})
        """, returned_order_ids)
        returned_status_total = Decimal(str(cursor.fetchone()[0] or "0.00"))

    # 4. che_returned_total
    # Fetch all settlements transactions and filter by order_date in range in Python
    cursor.execute("""
        SELECT order_date, debt, source, transaction_type_code
        FROM core_chetransaction
        WHERE source = 'settlements' AND transaction_type_code = 'Return'
    """)
    all_che = cursor.fetchall()
    che_returned_total = Decimal("0.00")
    for order_date_str, debt, source, tx_type in all_che:
        if order_date_str:
            order_date = parse_db_datetime(order_date_str)
            if min_date <= order_date <= max_date:
                che_returned_total += Decimal(str(debt or 0))

    returned_total = che_returned_total if che_returned_total > Decimal("0.00") else returned_status_total

    formula_net_sales = total_gross - cancelled_total - returned_total - total_discount
    toplam_ciro = max(formula_net_sales, Decimal("0.00"))

    print(f"--- Rapor: {min_date_str} - {max_date_str} ---")
    print(f"Total Gross Sales: ₺{total_gross:,.2f}")
    print(f"Total Discount   : ₺{total_discount:,.2f}")
    print(f"Cancelled Total  : ₺{cancelled_total:,.2f}")
    print(f"Returned Status  : ₺{returned_status_total:,.2f}")
    print(f"Returned CHE     : ₺{che_returned_total:,.2f}")
    print(f"Returned Total   : ₺{returned_total:,.2f}")
    print(f"Toplam Ciro      : ₺{toplam_ciro:,.2f}")
    print()

calculate_toplam_ciro("2026-04-01", "2026-04-30")
calculate_toplam_ciro("2026-04-23", "2026-05-23")
