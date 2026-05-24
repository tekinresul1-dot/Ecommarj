from core.models import Order
last_order = Order.objects.order_by('-order_date').first()
print('Last order date in DB:', last_order.order_date if last_order else 'No orders')
