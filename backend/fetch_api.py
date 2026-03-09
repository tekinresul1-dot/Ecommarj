import os
import django
import json
from datetime import datetime, timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import MarketplaceAccount
from core.services.trendyol_client import TrendyolApiClient
from core.utils.encryption import decrypt_value

acc = MarketplaceAccount.objects.first()
client = TrendyolApiClient(api_key=acc.api_key, api_secret=decrypt_value(acc.api_secret), seller_id=acc.seller_id)

start_date = datetime(2026, 3, 1, tzinfo=timezone.utc)
end_date = datetime.now(timezone.utc)

orders = client.fetch_orders(start_date, end_date)
print(f"Total packages from Trendyol: {len(orders)}")

for o in orders:
    pkg = o.get("shipmentPackageId", "")
    order_no = o.get("orderNumber", "")
    lines = o.get("lines", [])
    print(f"Package: {pkg}, Order: {order_no}, Total Lines: {len(lines)}")
    for l in lines:
        print(f"  Line: {l.get('id')}, SKU: {l.get('merchantSku')}, Price: {l.get('price')}, Amount: {l.get('amount')}, Status: {l.get('orderLineItemStatusName')}")
