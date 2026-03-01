import os
import django
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecompro_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import (
    Organization, MarketplaceAccount, Product, ProductVariant,
    Order, OrderItem, FinancialTransaction, FinancialTransactionType
)
from core.services.profit_calculator import ProfitCalculator

User = get_user_model()

def run():
    print("Seeding mock data for EcomPro...")

    # 1. Ensure user and organization exist
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Created default admin user")

    org, created = Organization.objects.get_or_create(name="Trendyol Demo Mağazası")
    
    # Kendi profiline bağla
    if hasattr(admin_user, 'profile'):
        admin_user.profile.organization = org
        admin_user.profile.save()

    account, _ = MarketplaceAccount.objects.get_or_create(
        organization=org,
        channel=MarketplaceAccount.Channel.TRENDYOL,
        seller_id="123456",
        defaults={
            "store_name": "Demo Trendyol Mağazası",
            "api_key": "mock_key",
            "api_secret": "mock_secret"
        }
    )

    # 2. Clear old mock data to avoid duplication
    Order.objects.filter(organization=org).delete()
    Product.objects.filter(organization=org).delete()

    # 3. Create Seed Products
    # Product 1: The screenshot example (2000 TL, Cost 750, Comm 21.5%, Cargo 95)
    p1, _ = Product.objects.get_or_create(
        organization=org,
        barcode="A132BLACK85",
        defaults={
            "marketplace_account": account,
            "title": "Siyah Dantelli Bralet Takım Seksi İç Çamaşırı Seti GM101",
            "category_name": "İç Giyim",
            "sale_price": Decimal("2000.00"),
            "vat_rate": Decimal("20.00"),
            "commission_rate": Decimal("21.50"),
            "initial_stock": 100,
            "current_stock": 15,
            "desi": Decimal("6.00"),
            "default_carrier": "Trendyol Express",
            "image_url": "https://cdn.dsmcdn.com/ty465/product/media/images/20220627/12/130104107/116246471/1/1_org_zoom.jpg"
        }
    )
    pv1, _ = ProductVariant.objects.get_or_create(product=p1, barcode=p1.barcode)

    # Product 2: Lower margin product
    p2, _ = Product.objects.get_or_create(
        organization=org,
        barcode="TSHIRT-W-01",
        defaults={
            "marketplace_account": account,
            "title": "Pamuklu Beyaz Oversize Tişört",
            "category_name": "Giyim",
            "sale_price": Decimal("350.00"),
            "vat_rate": Decimal("10.00"),
            "commission_rate": Decimal("15.00"),
            "initial_stock": 50,
            "current_stock": 2, # Critical Stock
            "desi": Decimal("2.00"),
            "default_carrier": "Yurtiçi Kargo",
            "image_url": "https://cdn.dsmcdn.com/mnresize/1200/1800/ty1019/product/media/images/prod/SPM/PIM/20211116/17/83a4fb24-8b6a-36fb-b0cf-eb6d05da1c66/1_org_zoom.jpg"
        }
    )
    pv2, _ = ProductVariant.objects.get_or_create(product=p2, barcode=p2.barcode)

    PRODUCT_COSTS = {
        p1.id: Decimal("750.00"),
        p2.id: Decimal("120.00")
    }

    # 4. Create Random Orders over the last 30 days
    total_orders_to_create = 45
    print(f"Generating {total_orders_to_create} mock orders...")

    now = timezone.now()
    
    for i in range(total_orders_to_create):
        days_ago = random.randint(0, 30)
        order_date = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        o = Order.objects.create(
            organization=org,
            marketplace_account=account,
            marketplace_order_id=f"MOCK-{100000 + i}",
            order_date=order_date,
            status=Order.Status.DELIVERED,
            channel=Order.Channel.TRENDYOL,
            country_code="TR"
        )
        
        # Pick a random product
        target_p = random.choice([p1, p1, p2]) # Weight p1 heavily
        target_pv = pv1 if target_p == p1 else pv2
        qty = 1

        sale_gross = target_p.sale_price * qty
        cost = PRODUCT_COSTS[target_p.id] * qty
        comm_rate = target_p.commission_rate
        vat_rate = target_p.vat_rate

        order_item = OrderItem.objects.create(
            order=o,
            product_variant=target_pv,
            marketplace_line_id=f"LINE-{100000 + i}",
            sku=target_p.barcode,
            quantity=qty,
            sale_price_gross=sale_gross,
            sale_price_net=sale_gross,
            applied_vat_rate=vat_rate,
            applied_commission_rate=comm_rate
        )

        # Before generating transactions, let's inject ONLY the known Product Cost.
        FinancialTransaction.objects.create(
            organization=org,
            order_item_ref=order_item,
            transaction_type=FinancialTransactionType.PRODUCT_COST.value,
            amount=cost,
            occurred_at=order_date
        )

        # Now let our engine calculate everything else dynamically. 
        # (It will look up CargoPricing since there is no SHIPPING_FEE transaction)
        calc_result = ProfitCalculator.calculate_for_order_item(order_item)

        breakdown = calc_result["breakdown"]

        for tx_type, amount in breakdown.items():
            # Don't duplicate Product Cost
            if tx_type == FinancialTransactionType.PRODUCT_COST.value:
                continue
            FinancialTransaction.objects.create(
                organization=org,
                order_item_ref=order_item,
                transaction_type=tx_type,
                amount=amount, 
                occurred_at=order_date
            )
            
        print(f"Created Order {o.marketplace_order_id} (Cargo: {calc_result['breakdown'].get('SHIPPING_FEE', 0)} TL, Net Profit: {calc_result['net_profit']} TL)")

    print("Success! Mock DB populated.")

if __name__ == '__main__':
    run()
