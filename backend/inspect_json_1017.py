import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order, UserProfile
from core.views import OrderListView, format_date_tr
from rest_framework.test import APIRequestFactory, force_authenticate
from decimal import Decimal

# Helper to serialize Decimal
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

factory = APIRequestFactory()
user_profile = UserProfile.objects.filter(organization_id=4).first()
request = factory.get('/api/orders/')
force_authenticate(request, user=user_profile.user)

order = Order.objects.get(pk=1017)
view = OrderListView()
view.request = request

# Mimic the loop in OrderListView
total_gross = Decimal("0.00")
total_net_profit = Decimal("0.00")
cum_breakdown = {
    "product_cost": Decimal("0.00"),
    "commission": Decimal("0.00"),
    "shipping": Decimal("0.00"),
    "service_fee": Decimal("0.00"),
    "withholding": Decimal("0.00"),
    "vat_output": Decimal("0.00"),
    "return_loss": Decimal("0.00"),
}

from core.services.profit_calculator import ProfitCalculator
for item in order.items.all():
    res = ProfitCalculator.calculate_for_order_item(item)
    total_gross += res["gross_revenue"]
    total_net_profit += res["net_profit"]
    # Adjust breakdown keys as per calculation
    cum_breakdown["product_cost"] += res["breakdown"].get("PRODUCT_COST", Decimal("0"))
    cum_breakdown["commission"] += res["breakdown"].get("COMMISSION", Decimal("0"))
    cum_breakdown["shipping"] += res["breakdown"].get("SHIPPING_FEE", Decimal("0"))
    cum_breakdown["service_fee"] += res["breakdown"].get("SERVICE_FEE", Decimal("0"))
    cum_breakdown["withholding"] += res["breakdown"].get("WITHHOLDING", Decimal("0"))
    cum_breakdown["vat_output"] += res["breakdown"].get("VAT_OUTPUT", Decimal("0"))
    cum_breakdown["return_loss"] += res["breakdown"].get("RETURN_LOSS", Decimal("0"))

# Profit calculations
profit_margin = Decimal("0.00")
if total_gross > Decimal("0.00"):
    profit_margin = round((total_net_profit / total_gross) * Decimal("100.00"), 2)

profit_on_cost = Decimal("0.00")
if cum_breakdown["product_cost"] > Decimal("0.00"):
    profit_on_cost = round((total_net_profit / cum_breakdown["product_cost"]) * Decimal("100.00"), 2)

data = {
    "id": order.id,
    "order_number": order.marketplace_order_id,
    "order_date": format_date_tr(order.order_date),
    "status": order.status,
    "is_micro_export": order.channel == 'micro_export',
    "total_gross": str(total_gross),
    "total_profit": str(total_net_profit),
    "profit_margin": str(profit_margin),
    "profit_on_cost": str(profit_on_cost),
}

print(json.dumps(data, indent=2))
