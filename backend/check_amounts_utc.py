from core.models import Order, OrderItem
from django.utils import timezone
from django.db.models import Sum
import datetime

# Test UTC
min_d_utc = datetime.datetime(2026, 4, 24, 0, 0, 0, tzinfo=datetime.timezone.utc)
max_d_utc = datetime.datetime(2026, 5, 24, 23, 59, 59, tzinfo=datetime.timezone.utc)

qs_utc = Order.objects.filter(organization_id=1, order_date__gte=min_d_utc, order_date__lte=max_d_utc)

print("Orders (UTC):", qs_utc.count())

GROSS_STATUSES = ['Created', 'Picking', 'Shipped', 'Delivered', 'Returned']
gross_items_utc = OrderItem.objects.filter(order__in=qs_utc, status__in=GROSS_STATUSES)
print("Gross Qty (UTC):", gross_items_utc.aggregate(qty=Sum("quantity"))["qty"])
print("Gross Amt (UTC):", gross_items_utc.aggregate(amt=Sum("sale_price_gross"))["amt"])
