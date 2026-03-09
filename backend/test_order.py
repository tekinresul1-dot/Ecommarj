import os
import django
from datetime import datetime
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import MarketplaceAccount
from core.services.trendyol_adapter import TrendyolAdapter

accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")

found = 0
target_orders = ["10980060619", "10972062950", "10992325266", "10981445821", "10940255299"]
start_ms = int(datetime(2026, 2, 10).timestamp() * 1000)
end_ms = int(datetime(2026, 2, 28).timestamp() * 1000)

for acc in accounts:
    print(f"Trying account: {acc.seller_id}")
    try:
        adapter = TrendyolAdapter(acc.api_key, acc.api_secret, acc.seller_id)
        orders, errors = adapter.fetch_orders(start_date_ms=start_ms, end_date_ms=end_ms)
        
        for o in orders:
            if str(o.get('orderNumber')) in target_orders:
                print(f"\nOrder: {o.get('orderNumber')}")
                print(f"cargoProviderName (root): {o.get('cargoProviderName')}")
                c_detail = o.get('cargoDetail', {})
                print(f"cargoDetail.cargoProviderName: {c_detail.get('cargoProviderName') if isinstance(c_detail, dict) else c_detail}")
                
                # Package level details
                lines = o.get('lines', [])
                for line in lines:
                     print(f" - Line {line.get('id')}: cargoProviderName: {line.get('cargoProviderName')}")

                found += 1
    except Exception as e:
        print(f"Error for account {acc.seller_id}: {e}")

if found == 0:
    print("Could not find the target orders in the fetched range across active accounts.")
