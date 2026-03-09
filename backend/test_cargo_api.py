import os
import django
from datetime import datetime, timedelta
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import MarketplaceAccount
from core.services.trendyol_adapter import TrendyolAdapter
from django.utils import timezone

acc = MarketplaceAccount.objects.get(id=15)
# Use correct arguments for TrendyolAdapter
adapter = TrendyolAdapter(api_key=acc.api_key, api_secret=acc.api_secret, seller_id=acc.seller_id)

end_date = timezone.now()
start_date = end_date - timedelta(days=30)
start_ms = int(start_date.timestamp() * 1000)
end_ms = int(end_date.timestamp() * 1000)

print(f"Fetching OtherFinancials for Account {acc.id} from {start_date} to {end_date}")
financials = adapter.fetch_other_financials(start_ms, end_ms)

print(f"Found {len(financials)} total financial items.")
cargo_invoices = [f for f in financials if f.get("transactionType") in ["DeductionInvoices", "Kargo Faturası", "Kargo Fatura"]]
print(f"Found {len(cargo_invoices)} cargo-related items.")

if cargo_invoices:
    for inv in cargo_invoices[:5]:
        inv_id = inv.get('id') or inv.get('invoiceSerialNumber')
        print(f"Invoice ID: {inv_id}, Type: {inv.get('transactionType')}")
        # Try to fetch items for this one
        items = adapter.fetch_cargo_invoice_items(inv_id)
        print(f"  Items count: {len(items)}")
        if items:
            print(f"  Sample item: {json.dumps(items[0], indent=2)}")
