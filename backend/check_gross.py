from core.models import OrderItem

items = OrderItem.objects.filter(discount__gt=0).order_by('-id')[:5]
for item in items:
    print(f"OrderItem {item.id} - Qty: {item.quantity}")
    print(f"Gross: {item.sale_price_gross}, Net: {item.sale_price_net}, Discount: {item.discount}")
    print(f"Expected Gross (if Net+Discount): {item.sale_price_net + item.discount}")
    print("---")
