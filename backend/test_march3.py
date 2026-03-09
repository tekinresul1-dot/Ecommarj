import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order, OrderItem

march_orders = Order.objects.filter(order_date__year=2026, order_date__month=3)
for o in march_orders:
    print(o.marketplace_order_id, o.order_number, o.package_id, o.status)
    for i in o.items.all():
        print(f"  Item: {i.sku}, Net: {i.sale_price_net}, Gross: {i.sale_price_gross}")
