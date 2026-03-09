import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import MarketplaceAccount
from core.services.trendyol_adapter import TrendyolAdapter

acc = MarketplaceAccount.objects.get(id=15)
adapter = TrendyolAdapter(api_key=acc.api_key, api_secret=acc.api_secret, seller_id=acc.seller_id)

url = f"{adapter.BASE_URL}/shipment-packages"
params = {"orderNumber": "10992325266"}

resp = adapter._make_request(url, params, operation="InspectOrder")
if resp.status_code == 200:
    data = resp.json()
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {resp.status_code}, {resp.text}")
