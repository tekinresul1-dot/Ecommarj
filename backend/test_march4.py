import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import OrderItem

items = OrderItem.objects.filter(order__order_date__year=2026, order__order_date__month=3).exclude(status__in=["Cancelled", "Returned", "UnSupplied"])
tot_net = 0
for i in items:
    print(f"ID: {i.id}, Order: {i.order.order_number}, Line ID: '{i.marketplace_line_id}', Net: {i.sale_price_net}, Qty: {i.quantity}")
    tot_net += i.sale_price_net
print(f"Total Net: {tot_net}")
