import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order, OrderItem

orders = Order.objects.filter(order_date__year=2026, order_date__month=3, channel__in=["trendyol", "micro_export"])
print(f"Total Orders in March 2026: {orders.count()}")

gross_sum = Decimal("0.00")
net_sum = Decimal("0.00")

for o in orders:
    for i in o.items.all():
        if i.status not in ["Cancelled", "Returned", "UnSupplied"]:
            gross_sum += i.sale_price_gross
            net_sum += i.sale_price_net
            print(f"Order: {o.order_number}, ID: {o.id}, item_status: {i.status}, gross: {i.sale_price_gross}, net: {i.sale_price_net}, quantity: {i.quantity}")

print(f"Gross Sum: {gross_sum}")
print(f"Net Sum: {net_sum}")
