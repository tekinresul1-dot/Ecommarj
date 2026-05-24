import os, django, requests
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommarj_backend.settings")
django.setup()
from core.models import MarketplaceAccount
from core.utils.encryption import decrypt_value
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.filter(email="mahfelce@gmail.com").first()
account = MarketplaceAccount.objects.filter(organization=user.profile.organization, is_active=True).first()
api_key = decrypt_value(account.api_key)
api_secret = decrypt_value(account.api_secret)

for order_num in ["11177156335", "11099926593"]:
    url = f"https://api.trendyol.com/sapigw/suppliers/{account.seller_id}/orders?orderNumber={order_num}"
    res = requests.get(url, auth=(api_key, api_secret))
    if res.status_code == 200:
        content = res.json().get("content", [])
        print(f"API {order_num}: {len(content)} pkgs")
        for p in content:
            print(f"  Pkg: {p.get('id')} -> {p.get('status')}")
            for l in p.get('lines', []):
                print(f"    Line: {l.get('id')} -> {l.get('orderLineItemStatusName')}")
    else:
        print(f"Failed {order_num}: {res.status_code}")
