import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecompro_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from core.models import Organization, UserProfile, MarketplaceAccount, Order, OrderItem, FinancialTransaction, FinancialTransactionType
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
if not User.objects.filter(email='demo@ecompro.com').exists():
    user = User.objects.create_user(username='demo@ecompro.com', email='demo@ecompro.com', password='password123', first_name='Ozan', last_name='Candemir')
    org = Organization.objects.create(name="EcomPro Test A.Ş.")
    UserProfile.objects.create(user=user, organization=org)

    acc = MarketplaceAccount.objects.create(organization=org, store_name="Trendyol TR", seller_id="444")
    micro_acc = MarketplaceAccount.objects.create(organization=org, channel=MarketplaceAccount.Channel.MICRO_EXPORT, store_name="Micro Export Global", seller_id="555")

    now = timezone.now()
    
    # Trendyol orders
    for i in range(10):
        o = Order.objects.create(organization=org, marketplace_account=acc, marketplace_order_id=f"T{i}", order_date=now - timedelta(days=i), status="Delivered")
        item = OrderItem.objects.create(order=o, sku=f"SKU-TR-{i}", sale_price_gross=Decimal("200"), sale_price_net=Decimal("150"), quantity=1)
        FinancialTransaction.objects.create(organization=org, order_item_ref=item, transaction_type=FinancialTransactionType.PRODUCT_COST, amount=Decimal("40"), occurred_at=now)
        FinancialTransaction.objects.create(organization=org, order_item_ref=item, transaction_type=FinancialTransactionType.COMMISSION, amount=Decimal("22.5"), occurred_at=now)
        FinancialTransaction.objects.create(organization=org, order_item_ref=item, transaction_type=FinancialTransactionType.SHIPPING_FEE, amount=Decimal("15"), occurred_at=now)
        if i % 3 == 0:
            FinancialTransaction.objects.create(organization=org, order_item_ref=item, transaction_type=FinancialTransactionType.RETURN_LOSS, amount=Decimal("12"), occurred_at=now)

    # Micro orders
    countries = ["AZ", "AE", "SA", "RO", "BG"]
    for i, country in enumerate(countries):
        o = Order.objects.create(organization=org, channel="micro_export", country_code=country, marketplace_account=micro_acc, marketplace_order_id=f"M{i}", order_date=now - timedelta(days=i), status="Delivered")
        item = OrderItem.objects.create(order=o, sku=f"SKU-MC-{i}", sale_price_gross=Decimal("1000"), sale_price_net=Decimal("800"), quantity=1)
        FinancialTransaction.objects.create(organization=org, order_item_ref=item, transaction_type=FinancialTransactionType.PRODUCT_COST, amount=Decimal("200"), occurred_at=now)
        FinancialTransaction.objects.create(organization=org, order_item_ref=item, transaction_type=FinancialTransactionType.COMMISSION, amount=Decimal("120"), occurred_at=now)
        FinancialTransaction.objects.create(organization=org, order_item_ref=item, transaction_type=FinancialTransactionType.SHIPPING_FEE, amount=Decimal("250"), occurred_at=now)

print("Seed done")
