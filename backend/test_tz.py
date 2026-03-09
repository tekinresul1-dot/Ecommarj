import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order
from django.utils import timezone

orders = Order.objects.all()
for o in orders:
    print(f"Order: {o.order_number}, Date: {o.order_date}, Status: {o.status}")
