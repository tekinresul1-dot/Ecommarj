import os
import django
from decimal import Decimal
from django.db import models as django_models

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order, OrderItem, Organization

org = Organization.objects.first()

orders_qs = Order.objects.filter(
    organization=org, channel__in=["trendyol", "micro_export"],
    order_date__year=2026, order_date__month=3
)

active_orders_qs = orders_qs.exclude(status__in=["Cancelled", "Returned", "UnSupplied"])

active_items_qs = OrderItem.objects.filter(
    order__in=active_orders_qs
).exclude(status__in=["Cancelled", "Returned", "UnSupplied"])

revenue_agg = active_items_qs.aggregate(
    total_gross=django_models.Sum("sale_price_gross"),
    total_net=django_models.Sum("sale_price_net"),
    total_items=django_models.Count("id"),
)

print(f"Total Gross: {revenue_agg['total_gross']}")
print(f"Total Net:   {revenue_agg['total_net']}")
print(f"Total Items: {revenue_agg['total_items']}")

for item in active_items_qs:
    print(f"Item ID: {item.id}, Order: {item.order.order_number}, Net: {item.sale_price_net}, Qty: {item.quantity}")
