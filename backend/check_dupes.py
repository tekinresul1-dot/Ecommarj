import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order
qs = Order.objects.filter(order_number='10981445821')
print(f"Count: {qs.count()}")
for o in qs:
    print(f"PK: {o.pk}, PackageID: {o.package_id}, Carrier: '{o.cargo_provider_name}', Status: {o.status}")
