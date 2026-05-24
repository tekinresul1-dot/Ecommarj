from core.models import Order, OrderItem
from django.utils import timezone
from django.db.models import Sum, Q
import datetime

min_d = timezone.make_aware(datetime.datetime(2026,4,1))
max_d = timezone.make_aware(datetime.datetime(2026,4,30,23,59,59))

qs_order_date = Order.objects.filter(organization_id=1, order_date__gte=min_d, order_date__lte=max_d)

GROSS_STATUSES = ['Created', 'Picking', 'Shipped', 'Delivered', 'Returned', 'Cancelled', 'UnSupplied']
CANCEL_STATUSES = ['Cancelled', 'UnSupplied']
RETURN_STATUSES = ['Returned']
ACTIVE_STATUSES = ["Delivered", "Shipped", "Created", "Picking"]

all_items = OrderItem.objects.filter(order__in=qs_order_date, status__in=GROSS_STATUSES)

gross = all_items.aggregate(amt=Sum('sale_price_gross'))['amt'] or 0
discount_all = all_items.aggregate(amt=Sum('discount'))['amt'] or 0

cancel = all_items.filter(status__in=CANCEL_STATUSES)
cancel_gross = cancel.aggregate(amt=Sum('sale_price_gross'))['amt'] or 0

ret = all_items.filter(status__in=RETURN_STATUSES)
ret_gross = ret.aggregate(amt=Sum('sale_price_gross'))['amt'] or 0

from core.models import CheTransaction
che_returned_total = CheTransaction.objects.filter(
    organization_id=1,
    source=CheTransaction.SOURCE_SETTLEMENTS,
    transaction_type_code="Return",
    order_date__gte=min_d,
    order_date__lte=max_d,
).aggregate(total=Sum("debt"))["total"] or 0

ret_total = che_returned_total if che_returned_total > ret_gross else ret_gross

net = float(gross) - float(cancel_gross) - float(ret_total) - float(discount_all)

active_items = all_items.filter(status__in=ACTIVE_STATUSES)
active_net = active_items.aggregate(amt=Sum('sale_price_net'))['amt'] or 0

print(f"OrderDate Gross Amt: {gross}")
print(f"OrderDate Cancel Amt (Gross): {cancel_gross}")
print(f"OrderDate Return Amt (Gross): {ret_gross} | CHE: {che_returned_total}")
print(f"OrderDate Discount (All): {discount_all}")
print(f"OrderDate NET (Trendyol formula): {net}")
print(f"OrderDate NET (Active Sum sale_price_net): {active_net}")
