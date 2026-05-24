import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import MarketplaceAccount, Order, OrderItem
from django.contrib.auth import get_user_model
from core.utils.encryption import decrypt_value
from core.services.order_sync import TrendyolOrderSyncService

User = get_user_model()
user = User.objects.filter(email='mahfelce@gmail.com').first()
if not user:
    print("User mahfelce@gmail.com not found")
    exit(1)

account = MarketplaceAccount.objects.filter(organization=user.profile.organization, is_active=True).first()
if not account:
    print("Account not found")
    exit(1)

try:
    api_key = decrypt_value(account.api_key)
    api_secret = decrypt_value(account.api_secret)
    print("Credentials successfully decrypted.")
except Exception as e:
    print(f"Failed to decrypt credentials: {e}")
    api_key = None

orders = Order.objects.filter(
    organization=user.profile.organization,
    order_number__in=["11177156335", "11099926593"]
).order_by('order_number')

print(f"\n--- LOCAL DB ORDERS ({orders.count()}) ---")
for o in orders:
    print(f"\nOrder: {o.order_number} | Pkg: {o.package_id}")
    print(f"  Dates: order={o.order_date}, last_modified={o.last_modified_date}, created={o.created_at}")
    print(f"  Status: order_status={o.status}")
    print(f"  Items ({o.items.count()}):")
    for item in o.items.all():
        print(f"    Line: {getattr(item, 'marketplace_line_id', getattr(item, 'id'))} | Status: {item.status}")
        print(f"    Flags: is_cancelled={getattr(item, 'is_cancelled', False)}, is_returned={getattr(item, 'is_returned', False)}")

if api_key:
    import requests
    from requests.auth import HTTPBasicAuth
    print("\n--- TRENDYOL API ---")
    svc = TrendyolOrderSyncService(account)
    for order_num in ["11177156335", "11099926593"]:
        url = f"https://api.trendyol.com/sapigw/suppliers/{account.seller_id}/orders?orderNumber={order_num}"
        res = requests.get(url, headers=svc._get_headers())
        if res.status_code == 200:
            data = res.json()
            content = data.get("content", [])
            print(f"\nTrendyol response for {order_num}: {len(content)} packages found")
            for pkg in content:
                print(f"  Package ID: {pkg.get('id')} - Status: {pkg.get('status')}")
                for line in pkg.get("lines", []):
                    print(f"    Line {line.get('id')} | Status {line.get('orderLineItemStatusName')}")
        else:
            print(f"Failed to fetch {order_num}: {res.status_code} - {res.text}")
