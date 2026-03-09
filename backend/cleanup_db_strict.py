import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order

mar_orders = Order.objects.filter(order_date__year=2026, order_date__month=3).order_by('id')

seen_packages = set()
for o in mar_orders:
    # If package_id is empty, consider it a duplicate to be safe 
    # (unless it's the only one, but we have the real ones anyway)
    if not o.package_id:
        print(f"Deleting empty package order {o.id}")
        o.delete()
        continue
        
    if o.package_id in seen_packages:
        print(f"Deleting duplicate order {o.id} - package: {o.package_id}")
        o.delete()
    else:
        seen_packages.add(o.package_id)

print("--- FINAL CLEAN MARCH ORDERS ---")
from datetime import datetime, timezone
mar_orders = Order.objects.filter(order_date__year=2026, order_date__month=3)
for o in mar_orders:
    print(f"Order: {o.order_number}, Package: {o.package_id}")
    for i in o.items.all():
        print(f"  Line: {i.marketplace_line_id}, Net: {i.sale_price_net}")
