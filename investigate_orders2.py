import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()
from core.models import Order
orders = Order.objects.filter(order_number__in=["11177156335", "11099926593"]).order_by('order_number')
for o in orders:
    print(f"{o.order_number} | {o.package_id} | {o.status} | Gross: {o.package_gross_amount} | Net: {o.net_amount}")
