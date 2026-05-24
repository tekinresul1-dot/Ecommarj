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

DASHBOARD_REVENUE_STATUSES = ["Delivered", "Shipped"]
items = OrderItem.objects.filter(order__in=qs_fallback, status__in=DASHBOARD_REVENUE_STATUSES)
print("Delivered/Shipped Gross:", items.aggregate(amt=Sum('sale_price_gross'))['amt'])
print("Delivered/Shipped Net:", items.aggregate(amt=Sum('sale_price_net'))['amt'])

all_sold_items = OrderItem.objects.filter(order__in=qs_fallback, status__in=["Delivered", "Shipped", "Created", "Picking"])
print("All Sold Gross:", all_sold_items.aggregate(amt=Sum('sale_price_gross'))['amt'])
print("All Sold Net:", all_sold_items.aggregate(amt=Sum('sale_price_net'))['amt'])

