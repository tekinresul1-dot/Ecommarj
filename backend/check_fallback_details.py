from core.models import Order, OrderItem
from django.utils import timezone
from django.db.models import Sum, Q
import datetime

min_d = timezone.make_aware(datetime.datetime(2026,4,24))
max_d = timezone.make_aware(datetime.datetime(2026,5,24,23,59,59))

qs_fallback = Order.objects.filter(organization_id=1).filter(
    Q(last_modified_date__gte=min_d, last_modified_date__lte=max_d) |
    Q(last_modified_date__isnull=True, order_date__gte=min_d, order_date__lte=max_d)
)

GROSS_STATUSES = ['Created', 'Picking', 'Shipped', 'Delivered', 'Returned', 'Cancelled', 'UnSupplied']
CANCEL_STATUSES = ['Cancelled', 'UnSupplied']
RETURN_STATUSES = ['Returned']

all_items = OrderItem.objects.filter(order__in=qs_fallback, status__in=GROSS_STATUSES)

gross = all_items.aggregate(amt=Sum('sale_price_gross'))['amt']
discount_all = all_items.aggregate(amt=Sum('discount'))['amt']

cancel = all_items.filter(status__in=CANCEL_STATUSES)
cancel_gross = cancel.aggregate(amt=Sum('sale_price_gross'))['amt'] or 0
cancel_discount = cancel.aggregate(amt=Sum('discount'))['amt'] or 0

ret = all_items.filter(status__in=RETURN_STATUSES)
ret_gross = ret.aggregate(amt=Sum('sale_price_gross'))['amt'] or 0

active_items = all_items.exclude(status__in=CANCEL_STATUSES + RETURN_STATUSES)
active_discount = active_items.aggregate(amt=Sum('discount'))['amt'] or 0

print(f"Fallback Gross Amt: {gross}")
print(f"Fallback Cancel Amt (Gross): {cancel_gross}")
print(f"Fallback Return Amt (Gross): {ret_gross}")
print(f"Fallback Discount (All): {discount_all}")
print(f"Fallback Discount (Active Only): {active_discount}")

net_if_active_disc = float(gross) - float(cancel_gross) - float(ret_gross) - float(active_discount)
net_if_all_disc = float(gross) - float(cancel_gross) - float(ret_gross) - float(discount_all)

print(f"Net if we subtract Active Discount: {net_if_active_disc}")
print(f"Net if we subtract All Discount: {net_if_all_disc}")

