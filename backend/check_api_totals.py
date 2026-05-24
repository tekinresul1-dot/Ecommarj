from core.models import MarketplaceAccount
from core.services.trendyol_adapter import TrendyolAdapter
import datetime
from django.utils import timezone

account = MarketplaceAccount.objects.get(organization_id=1)
from core.utils.encryption import decrypt_value
adapter = TrendyolAdapter(
    api_key=decrypt_value(account.api_key),
    api_secret=decrypt_value(account.api_secret),
    seller_id=account.seller_id
)

min_d = datetime.datetime(2026,4,24, tzinfo=datetime.timezone.utc)
max_d = datetime.datetime(2026,5,24,23,59,59, tzinfo=datetime.timezone.utc)

start_ms = int(min_d.timestamp() * 1000)
end_ms = int(max_d.timestamp() * 1000)

print(f"Fetching from {min_d} to {max_d}")
orders = adapter.fetch_orders(start_date_ms=start_ms, end_date_ms=end_ms)

unique_packages = set()
total_qty = 0
total_gross = 0

for o in orders:
    unique_packages.add(o.get('shipmentPackageId') or o.get('id'))
    for line in o.get('lines', []):
        qty = int(line.get('quantity', 1))
        amount = float(line.get('amount') or 0)
        if amount > 0:
            gross = amount
        else:
            gross = float(line.get('price') or line.get('lineItemPrice') or 0) * qty
        
        total_qty += qty
        total_gross += gross

print(f"Unique Packages API: {len(unique_packages)}")
print(f"Total Qty API: {total_qty}")
print(f"Total Gross API: {total_gross}")

