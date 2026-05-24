from core.models import OrderItem
from pprint import pprint

items = OrderItem.objects.filter(order__organization_id=1).order_by('-id')[:5]
for item in items:
    print(f"OrderItem {item.id} - Qty: {item.quantity}")
    print(f"Gross: {item.sale_price_gross}, Net: {item.sale_price_net}, Discount: {item.discount}")
    print("---")
