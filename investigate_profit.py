import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order
from decimal import Decimal

order_num = "11255326314"
orders = Order.objects.filter(order_number=order_num)

print(f"--- ANALYZING ORDER {order_num} ---")
for o in orders:
    print(f"\nOrder: {o.id} | Pkg: {o.package_id} | Status: {o.status}")
    print(f"Pkg Gross: {o.package_gross_amount} | Pkg Discount: {o.package_total_discount}")
    print(f"Cargo Tracking: {o.cargo_tracking_number} | Cost: {getattr(o, 'cargo_cost', 'N/A')}")
    
    # Try to see what fields exist on OrderItem
    for item in o.items.all():
        fields = [f.name for f in item._meta.get_fields() if not f.is_relation and f.name != 'raw_payload']
        item_data = {f: getattr(item, f) for f in fields}
        print(f"  Line {item_data.get('marketplace_line_id', item.id)} fields: {item_data}")
        
    try:
        from core.services.profit_calculator import calculate_order_profit
        profit_res = calculate_order_profit(o)
        print(f"  Profit Calc: {profit_res}")
    except Exception as e:
        print(f"  calculate_order_profit error: {e}")

