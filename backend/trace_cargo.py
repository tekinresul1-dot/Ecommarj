import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order
from core.services.profit_calculator import ProfitCalculator

order = Order.objects.get(order_number='10981445821')
print(f"Order: {order.order_number}")
print(f"Carrier in DB: '{order.cargo_provider_name}'")

for item in order.items.all():
    print(f"\nItem ID: {item.id}, Sku: {item.sku}")
    
    # Trace the calculation
    print("--- TRACING CARGO CALCULATION ---")
    product = item.product_variant.product
    variant = item.product_variant
    
    active_desi = variant.desi if variant.desi is not None else product.desi
    print(f"Active Desi: {active_desi}")
    
    raw_carrier = order.cargo_provider_name if order.cargo_provider_name else product.default_carrier
    print(f"Raw Carrier: '{raw_carrier}'")
    
    def normalize_carrier(name: str):
        if not name: return ""
        name = name.lower()
        if "yurtiçi" in name or "yurtici" in name: return "Yurtiçi Kargo"
        if "mng" in name: return "MNG Kargo"
        if "aras" in name: return "Aras Kargo"
        if "sürat" in name or "surat" in name: return "Sürat Kargo"
        if "trendyol express" in name or "tex" in name: return "Trendyol Express"
        if "ptt" in name: return "PTT Kargo"
        return name
    
    carrier = normalize_carrier(raw_carrier)
    print(f"Normalized Carrier: '{carrier}'")
    
    # Get profit info
    profit_info = ProfitCalculator.calculate_for_order_item(item)
    print(f"Final Profit Info SHIPPING_FEE: {profit_info['breakdown'].get('SHIPPING_FEE')}")
