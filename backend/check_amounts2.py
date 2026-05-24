from core.models import Order, OrderItem
from django.utils import timezone
from django.db.models import Sum, Q
import datetime

min_d = timezone.make_aware(datetime.datetime(2026,4,24))
max_d = timezone.make_aware(datetime.datetime(2026,5,24,23,59,59))

qs_fallback = Order.objects.filter(
    organization_id=1
).filter(
    Q(last_modified_date__gte=min_d, last_modified_date__lte=max_d) |
    Q(last_modified_date__isnull=True, order_date__gte=min_d, order_date__lte=max_d)
)
print("Fallback Orders:", qs_fallback.count())

GROSS_STATUSES = ['Created', 'Picking', 'Shipped', 'Delivered', 'Returned']
CANCEL_STATUSES = ['Cancelled', 'UnSupplied']
RETURN_STATUSES = ['Returned']

gross_items_f = OrderItem.objects.filter(order__in=qs_fallback, status__in=GROSS_STATUSES)
print("Fallback Gross Qty:", gross_items_f.aggregate(qty=Sum("quantity"))["qty"])
print("Fallback Gross Amt:", gross_items_f.aggregate(amt=Sum("sale_price_gross"))["amt"])
