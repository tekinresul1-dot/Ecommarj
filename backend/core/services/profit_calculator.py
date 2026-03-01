from decimal import Decimal
from typing import Dict, Any
from core.models import OrderItem, FinancialTransactionType

# 26 Mart 2026 Kargo Barem Destek Tabloları (KDV Hariç)
TRENDYOL_BAREM_RATES = {
    "table1": { # Hızlı Teslimat veya Bugün Kargoda (Avantajlı)
        "0_199": {
            "Trendyol Express": Decimal("34.16"),
            "PTT Kargo": Decimal("34.16"),
            "Aras Kargo": Decimal("42.91"),
            "Sürat Kargo": Decimal("48.74"),
            "Kolay Gelsin": Decimal("51.24"),
            "DHL eCommerce": Decimal("52.08"),
            "Yurtiçi Kargo": Decimal("74.58"),
        },
        "200_349": {
            "Trendyol Express": Decimal("65.83"),
            "PTT Kargo": Decimal("65.83"),
            "Aras Kargo": Decimal("73.74"),
            "Sürat Kargo": Decimal("79.58"),
            "Kolay Gelsin": Decimal("82.08"),
            "DHL eCommerce": Decimal("82.91"),
            "Yurtiçi Kargo": Decimal("104.58"),
        }
    },
    "table2": { # 1 Günden Fazla Termin (Standart)
        "0_199": {
            "Trendyol Express": Decimal("64.58"),
            "PTT Kargo": Decimal("64.58"),
            "Aras Kargo": Decimal("71.66"),
            "Sürat Kargo": Decimal("77.49"),
            "Kolay Gelsin": Decimal("79.58"),
            "DHL eCommerce": Decimal("80.83"),
            "Yurtiçi Kargo": Decimal("101.24"),
        },
        "200_349": {
            "Trendyol Express": Decimal("72.91"),
            "PTT Kargo": Decimal("72.91"),
            "Aras Kargo": Decimal("79.99"),
            "Sürat Kargo": Decimal("85.83"),
            "Kolay Gelsin": Decimal("87.91"),
            "DHL eCommerce": Decimal("89.16"),
            "Yurtiçi Kargo": Decimal("109.58"),
        }
    }
}

class ProfitCalculator:
    """
    Sipariş kalemi (OrderItem) bazında kârlılık parçalanımı (Profit Breakdown) hesaplayan servis.
    Tüm işlemler `Decimal` ile yapılır.
    """

    @staticmethod
    def calculate_from_raw(
        sale_price_gross: Decimal,
        product_cost: Decimal,
        cargo_cost: Decimal,
        commission_rate: Decimal,
        vat_rate: Decimal,
        service_fee: Decimal = Decimal("13.19"), # Excel'den default
    ) -> Dict[str, Any]:
        """
        Ham verilerden (Satış, Kargo, Komisyon, KDV oranları) net kârlılığı Excel mantığıyla hesaplar.
        Tüm fiyatlar KDV dahil (Gross) girilmelidir.
        """
        from decimal import ROUND_HALF_UP

        def q(val: Decimal):
            return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 1. Satış ve Maliyet KDV'leri
        # KDV Hariç Tutar = KDV Dahil / (1 + KDV Oranı)
        # KDV Tutarı = KDV Hariç * KDV Oranı
        sale_kdv_factor = Decimal("1") + (vat_rate / Decimal("100"))
        satis_kdv = q((sale_price_gross / sale_kdv_factor) * (vat_rate / Decimal("100")))
        alis_kdv = q((product_cost / sale_kdv_factor) * (vat_rate / Decimal("100")))

        # 2. Komisyon Hesabı (Komisyon, KDV dahil satış tutarı üzerinden hesaplanır)
        commission_cost = q(sale_price_gross * (commission_rate / Decimal("100")))
        # Komisyon KDV'si %20 sabit alınır (Hizmet/Fatura)
        komisyon_kdv = q((commission_cost / Decimal("1.20")) * Decimal("0.20"))

        # 3. Kargo Hesabı
        # Kargo KDV'si %20 sabit alınır
        kargo_kdv = q((cargo_cost / Decimal("1.20")) * Decimal("0.20"))

        # 4. Hizmet Bedeli KDV'si (%20)
        hizmet_bedeli_kdv = q((service_fee / Decimal("1.20")) * Decimal("0.20"))

        # 5. Ödenmesi Gereken Net KDV
        net_kdv = q(satis_kdv - (alis_kdv + komisyon_kdv + kargo_kdv + hizmet_bedeli_kdv))

        # 6. Stopaj Kesintisi (Satış KDV Hariç tutarın yarısının %1'i veya muadil e-ticaret teşviki)
        # Excel: 2000 => 16.67 çıkmış. Satış Fiyatı üzerinden tahmini: (2000 / 1.20) * 0.01
        stopaj = q((sale_price_gross / Decimal("1.20")) * Decimal("0.01"))

        # 7. Net Kâr
        # Tüm KDV dahil maliyetler çıkıldıktan sonra, KDV farkı (Devlete Ödenecek KDV) da bir giderdir.
        # net_kdv negatifse (devreden kdv), zarar azaltıcı etki yapar. Bu yüzden çıkarılır (veya eksi eksi artı olur).
        net_profit = q(sale_price_gross - (product_cost + commission_cost + cargo_cost + service_fee + stopaj + net_kdv))
        
        # Breakdown Mapping
        breakdown = {
            FinancialTransactionType.PRODUCT_COST.value: product_cost,
            FinancialTransactionType.COMMISSION.value: commission_cost,
            FinancialTransactionType.SHIPPING_FEE.value: cargo_cost,
            FinancialTransactionType.SERVICE_FEE.value: service_fee,
            FinancialTransactionType.WITHHOLDING.value: stopaj,
            FinancialTransactionType.VAT_OUTPUT.value: net_kdv,
        }

        profit_margin = Decimal("0.00")
        if sale_price_gross > Decimal("0"):
            profit_margin = q((net_profit / sale_price_gross) * Decimal("100.00"))

        profit_on_cost = Decimal("0.00")
        if product_cost > Decimal("0"):
            profit_on_cost = q((net_profit / product_cost) * Decimal("100.00"))

        return {
            "gross_revenue": sale_price_gross,
            "net_revenue": sale_price_gross - (satis_kdv if satis_kdv > 0 else 0), # Muhasebesel net
            "total_costs": q(product_cost + commission_cost + cargo_cost + service_fee + stopaj + net_kdv),
            "net_profit": net_profit,
            "profit_margin": profit_margin,
            "profit_on_cost": profit_on_cost,
            "kdv_detail": {
                "satis_kdv": satis_kdv,
                "alis_kdv": alis_kdv,
                "kargo_kdv": kargo_kdv,
                "komisyon_kdv": komisyon_kdv,
                "hizmet_bedeli_kdv": hizmet_bedeli_kdv,
                "net_kdv": net_kdv
            },
            "breakdown": breakdown
        }

    @staticmethod
    def calculate_for_order_item(order_item: OrderItem) -> Dict[str, Any]:
        """
        Sisteme kayıtlı bir sipariş kalemi üzerinden model datalarını okuyarak yukarıdaki ham hesabı çağırır.
        """
        # Standart veriler
        sale_price_gross = order_item.sale_price_gross
        product_cost = Decimal("0.00")
        cargo_cost = Decimal("0.00")
        commission_rate = Decimal("0.00")
        vat_rate = Decimal("20.00")
        
        # Transactions'lardan çekebildiğimiz veriler
        for tx in order_item.transactions.all():
            if tx.transaction_type == FinancialTransactionType.PRODUCT_COST.value:
                product_cost = abs(tx.amount)
            elif tx.transaction_type == FinancialTransactionType.SHIPPING_FEE.value:
                cargo_cost = abs(tx.amount)
                
        # Ürün verisi varsa komisyon, vat ve tahmini kargoyu al
        if order_item.product_variant and order_item.product_variant.product:
            variant = order_item.product_variant
            product = variant.product
            
            commission_rate = product.commission_rate
            vat_rate = product.vat_rate
            
            # Variant-level cost overrides Transactions if Transaction isn't present
            if product_cost == Decimal("0.00") and variant.cost_price > Decimal("0.00"):
                product_cost = variant.cost_price
                # Not: Alış KDV'si için variant.cost_vat_rate kullanılabilir, fakat şu an calculate_from_raw statik %20 alis_kdv hesaplıyor. İleride orası da dinamikleştirilebilir.
            
            # Aşama 1 (Tahmini Kargo): Fatura kesilmemişse (Transaction yoksa) desiden hesapla
            if cargo_cost == Decimal("0.00"):
                from core.models import CargoPricing
                
                # Desi önceliği: Varyantta yazan desi, yoksa Üründe yazan desi
                active_desi = variant.desi if variant.desi is not None else product.desi
                
                # TRENDYOL BAREM DESTEK (26 Mart 2026) KONTROLÜ
                barem_applied = False
                if sale_price_gross < Decimal("350.00") and active_desi <= Decimal("10.00"):
                    # Table seçimi
                    target_table = "table1" if product.fast_delivery else "table2"
                    
                    # Fiyat aralığı (0-199 ya da 200-349)
                    price_range = "0_199" if sale_price_gross < Decimal("200.00") else "200_349"
                    
                    # Taşıyıcı kontrolü (Eğer tabloda yoksa barem destek uygulanmaz, normal fiyata düşer)
                    carrier = product.default_carrier
                    if carrier in TRENDYOL_BAREM_RATES[target_table][price_range]:
                        barem_price_kdv_haric = TRENDYOL_BAREM_RATES[target_table][price_range][carrier]
                        cargo_cost = barem_price_kdv_haric * Decimal("1.20")
                        barem_applied = True
                
                # Barem desteğine uygun değilse veya taşıyıcı listede yoksa normal veritabanından(Excel) çek
                if not barem_applied:
                    try:
                        pricing = CargoPricing.objects.get(carrier_name=product.default_carrier, desi=active_desi)
                        # KDV Hariç fiyat üzerine %20 ekleyerek Gross kargo bedeli
                        cargo_cost = pricing.price_without_vat * Decimal("1.20")
                    except CargoPricing.DoesNotExist:
                        pass

        return ProfitCalculator.calculate_from_raw(
            sale_price_gross=sale_price_gross,
            product_cost=product_cost,
            cargo_cost=cargo_cost,
            commission_rate=commission_rate,
            vat_rate=vat_rate
        )
