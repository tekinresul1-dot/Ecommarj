from core.models import Order, OrderItem
from django.utils import timezone
from django.db.models import Sum, Count
import datetime

min_d = timezone.make_aware(datetime.datetime(2026,4,24))
max_d = timezone.make_aware(datetime.datetime(2026,5,24,23,59,59))

qs = Order.objects.filter(organization_id=1, order_date__gte=min_d, order_date__lte=max_d)
print("Orders:", qs.count())

GROSS_STATUSES = ['Created', 'Picking', 'Shipped', 'Delivered', 'Returned']
CANCEL_STATUSES = ['Cancelled', 'UnSupplied']
RETURN_STATUSES = ['Returned']

gross_items = OrderItem.objects.filter(order__in=qs, status__in=GROSS_STATUSES)
print("Gross Qty:", gross_items.aggregate(qty=Sum("quantity"))["qty"])
print("Gross Amt:", gross_items.aggregate(amt=Sum("sale_price_gross"))["amt"])
print("Discount Amt:", gross_items.aggregate(amt=Sum("discount"))["amt"])

cancel_items = OrderItem.objects.filter(order__in=qs, status__in=CANCEL_STATUSES)
print("Cancel Qty:", cancel_items.aggregate(qty=Sum("quantity"))["qty"])
print("Cancel Amt:", cancel_items.aggregate(amt=Sum("sale_price_gross"))["amt"])

return_items = OrderItem.objects.filter(order__in=qs, status__in=RETURN_STATUSES)
print("Return Qty:", return_items.aggregate(qty=Sum("quantity"))["qty"])
print("Return Amt:", return_items.aggregate(amt=Sum("sale_price_gross"))["amt"])
