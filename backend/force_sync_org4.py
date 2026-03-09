import os
import django
from datetime import datetime, timedelta
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import MarketplaceAccount, Order
from core.services.sync_service import TrendyolSyncService

# Organization 4's account
acc = MarketplaceAccount.objects.get(id=15)
print(f"Syncing Account {acc.id} (Seller: {acc.seller_id}, Org: {acc.organization_id})")

service = TrendyolSyncService(acc)
service.sync_orders() # No args, defaults to 365 days sliding window
service.sync_cargo_invoices()

# Verify the specific problematic order for Org 4
o = Order.objects.filter(order_number='10981445821', organization_id=4).first()
if o:
    print(f"Order 10981445821 (Org 4) Carrier after sync: '{o.cargo_provider_name}'")
else:
    print("Order 10981445821 (Org 4) not found after sync.")
