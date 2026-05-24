from core.models import OrderItem, Order
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

created_picking = OrderItem.objects.filter(order__in=qs_fallback, status__in=['Created', 'Picking'])
print("Created/Picking Qty:", created_picking.aggregate(qty=Sum("quantity"))["qty"])
print("Created/Picking Amt:", created_picking.aggregate(amt=Sum("sale_price_gross"))["amt"])

qs_order_date = Order.objects.filter(
    organization_id=1, order_date__gte=min_d, order_date__lte=max_d
)
cp_order_date = OrderItem.objects.filter(order__in=qs_order_date, status__in=['Created', 'Picking'])
print("OrderDate Created/Picking Qty:", cp_order_date.aggregate(qty=Sum("quantity"))["qty"])
print("OrderDate Created/Picking Amt:", cp_order_date.aggregate(amt=Sum("sale_price_gross"))["amt"])
