import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order, OrderItem
from django.db.models import Count

duplicates = (
    Order.objects.values('package_id', 'organization')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

for dup in duplicates:
    orders = Order.objects.filter(
        package_id=dup['package_id'], 
        organization=dup['organization']
    ).order_by('id')
    
    # Keep the last one, delete the others
    orders_to_delete = orders[:-1]
    for o in orders_to_delete:
        print(f"Deleting duplicate order {o.id} - package: {o.package_id}")
        o.delete()

# Also manually drop orders with empty order_number if there is a duplicate that IS populated for the same package
empty_orders = Order.objects.filter(order_number="")
for empty_o in empty_orders:
    if empty_o.package_id:
        if Order.objects.filter(package_id=empty_o.package_id).exclude(id=empty_o.id).exists():
             empty_o.delete()
             print(f"Deleted empty order_number constraint violation {empty_o.id}")

# Now let's print all March orders to verify it's clean (6 items)
print("--- CLEAN MARCH ORDERS ---")
from datetime import datetime, timezone
mar_orders = Order.objects.filter(order_date__year=2026, order_date__month=3)
for o in mar_orders:
    print(f"Order: {o.order_number}, Package: {o.package_id}")
    for i in o.items.all():
        print(f"  Line: {i.marketplace_line_id}, Net: {i.sale_price_net}")
