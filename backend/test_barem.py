import os
import django
from decimal import Decimal

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.utils import timezone
from core.models import Order, OrderItem, Product, ProductVariant, CargoPricing, MarketplaceAccount, Organization, UserProfile
from django.contrib.auth.models import User
from core.services.profit_calculator import ProfitCalculator

def verify_barem():
    user, _ = User.objects.get_or_create(username="baremtester", defaults={"email": "test@barem.com"})
    prof, _ = UserProfile.objects.get_or_create(user=user)
    org, _ = Organization.objects.get_or_create(name="Barem Test Org")
    acc, _ = MarketplaceAccount.objects.get_or_create(organization=org, store_name="Trendyol Barem", channel="Trendyol")

    # 1. Create a dummy product and variant
    p, _ = Product.objects.get_or_create(title="Test Barem Product", marketplace_account=acc, organization=org, defaults={
        "barcode": "BAREM123",
        "marketplace_sku": "SKU_BAREM",
        "sale_price": Decimal("150.00"),
        "desi": Decimal("2.00"),
        "default_carrier": "Trendyol Express",
        "fast_delivery": False
    })
    
    v, _ = ProductVariant.objects.get_or_create(product=p, defaults={"barcode": "V_BAREM123"})
    
    # Create Dummy Order
    order = Order(
        marketplace_account=acc,
        organization=org,
        marketplace_order_id="TEST_BAREM_1",
        status="Shipped",
        order_date=timezone.now()
    )
    order.save()
    
    order_item = OrderItem(
        order=order,
        product_variant=v,
        sale_price_gross=Decimal("150.00")
    )
    order_item.save()

    print("--- CASE 1: 150 TL, 2 Desi, TEX, Standard Delivery (Table 2) ---")
    p.fast_delivery = False
    p.save()
    res1 = ProfitCalculator.calculate_for_order_item(order_item)
    print(f"Expected Cargo Cost (KDV Dahil): {Decimal('64.58') * Decimal('1.2')}")
    print(f"Calculated Cargo Cost: {res1['breakdown']['SHIPPING_FEE']}")
    
    print("\n--- CASE 2: 150 TL, 2 Desi, TEX, Fast Delivery (Table 1) ---")
    p.fast_delivery = True
    p.save()
    v.refresh_from_db()
    order_item.refresh_from_db()
    res2 = ProfitCalculator.calculate_for_order_item(order_item)
    print(f"Expected Cargo Cost (KDV Dahil): {Decimal('34.16') * Decimal('1.2')}")
    print(f"Calculated Cargo Cost: {res2['breakdown']['SHIPPING_FEE']}")
    
    print("\n--- CASE 3: 300 TL, 2 Desi, TEX, Fast Delivery (Table 1, 200-349 band) ---")
    order_item.sale_price_gross = Decimal("300.00")
    order_item.save()
    order_item.refresh_from_db()
    res3 = ProfitCalculator.calculate_for_order_item(order_item)
    print(f"Expected Cargo Cost (KDV Dahil): {Decimal('65.83') * Decimal('1.2')}")
    print(f"Calculated Cargo Cost: {res3['breakdown']['SHIPPING_FEE']}")
    
    print("\n--- CASE 4: 400 TL, 2 Desi, TEX (ABOVE 350 -> Should hit Excel CargoPricing DB) ---")
    order_item.sale_price_gross = Decimal("400.00")
    order_item.save()
    
    # Ensure there is an Excel mock entry for TEX 2 Desi for testing
    c, created = CargoPricing.objects.get_or_create(carrier_name="Trendyol Express", desi=Decimal("2.00"), defaults={"price_without_vat": Decimal("100.00")})
    if not created:
        c.price_without_vat = Decimal("100.00")
        c.save()
        
    res4 = ProfitCalculator.calculate_for_order_item(order_item)
    print(f"Expected Cargo Cost (from Excel KDV dahil): {Decimal('100.00') * Decimal('1.2')}")
    print(f"Calculated Cargo Cost: {res4['breakdown']['SHIPPING_FEE']}")

if __name__ == "__main__":
    verify_barem()
