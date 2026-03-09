import os
import django
from decimal import Decimal
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order
from core.services.profit_calculator import ProfitCalculator
from core.views import format_date_tr

# Replicate OrderListView logic for one order
order = Order.objects.filter(order_number='10981445821').first()
if not order:
    print("Order not found")
    exit()

print(f"Order: {order.order_number}")
print(f"Carrier (DB): '{order.cargo_provider_name}'")

cum_breakdown = {
    "product_cost": Decimal("0.00"),
    "commission": Decimal("0.00"),
    "shipping_fee": Decimal("0.00"),
    "service_fee": Decimal("0.00"),
    "withholding": Decimal("0.00"),
    "net_kdv": Decimal("0.00"),
    "satis_kdv": Decimal("0.00"),
    "alis_kdv": Decimal("0.00"),
    "kargo_kdv": Decimal("0.00"),
    "komisyon_kdv": Decimal("0.00"),
    "hizmet_bedeli_kdv": Decimal("0.00"),
}

for item in order.items.all():
    profit_info = ProfitCalculator.calculate_for_order_item(item)
    bd = profit_info["breakdown"]
    print(f"Item {item.id} breakdown shipping: {bd.get('SHIPPING_FEE')}")
    cum_breakdown["shipping_fee"] += bd.get("SHIPPING_FEE", Decimal("0.00"))

print(f"Final Aggregated Shipping Fee: {cum_breakdown['shipping_fee']}")
