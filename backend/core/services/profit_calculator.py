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

def _normalize_carrier(name: str) -> str:
    if not name: return ""
    n = name.lower()
    if "yurtiçi" in n or "yurtici" in n: return "Yurtiçi Kargo"
    if "mng" in n: return "MNG Kargo"
    if "aras" in n: return "Aras Kargo"
    if "sürat" in n or "surat" in n: return "Sürat Kargo"
    if "trendyol express" in n or "tex" in n: return "Trendyol Express"
    if "ptt" in n: return "PTT Kargo"
    if "hepsijet" in n: return "Hepsijet"
    if "kargoist" in n: return "Kargoist"
    if "kargom" in n: return "Kargom"
    if "kolay gelsin" in n or "kolaygelsin" in n: return "Kolay Gelsin"
    if "dhl" in n: return "DHL eCommerce"
    return name

# Hardcoded fallback — DB'deki CarrierFlatRate kullanılamadığında devreye girer.
# Tarifeyi değiştirmek için CarrierFlatRate DB kaydını güncelle (bu dict'e dokunma).
FALLBACK_CARGO_RATES_KDV_DAHIL = {
    "Yurtiçi Kargo":    Decimal("135.32"),  # Trendyol tarife Mar 2026
    "Aras Kargo":       Decimal("96.00"),
    "Sürat Kargo":      Decimal("103.00"),
    "Trendyol Express": Decimal("87.50"),
    "PTT Kargo":        Decimal("87.50"),
    "MNG Kargo":        Decimal("96.00"),
    "Kolay Gelsin":     Decimal("105.50"),
    "Hepsijet":         Decimal("90.00"),
    "DHL eCommerce":    Decimal("107.00"),
    "Kargoist":         Decimal("90.00"),
    "Kargom":           Decimal("90.00"),
}


def _get_carrier_flat_rate(carrier: str) -> Decimal:
    """DB'deki CarrierFlatRate'i okur; bulunamazsa FALLBACK dict'e düşer."""
    try:
        from core.models import CarrierFlatRate
        return CarrierFlatRate.objects.get(carrier_name=carrier).rate_kdv_dahil
    except Exception:
        return FALLBACK_CARGO_RATES_KDV_DAHIL.get(carrier, Decimal("85.00"))


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
        is_micro_export: bool = False,
        sale_price_net: Decimal = None,
        is_returned: bool = False,
    ) -> Dict[str, Any]:
        """
        Ham verilerden (Satış, Kargo, Komisyon, KDV oranları) net kârlılığı Excel mantığıyla hesaplar.
        Tüm fiyatlar KDV dahil (Gross) girilmelidir.
        """
        from decimal import ROUND_HALF_UP
        
        def q(val: Decimal):
            return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # İndirimli fiyat (sale_price_net) Trendyol'un gerçek hakediş ve komisyon baz aldığı tutardır.
        active_sale_price = sale_price_net if sale_price_net is not None else sale_price_gross
        discount_amount = sale_price_gross - active_sale_price

        # 1. Satış ve Maliyet KDV'leri
        sale_kdv_factor = Decimal("1") + (vat_rate / Decimal("100"))
        
        if is_micro_export:
            satis_kdv = Decimal("0.00")
        else:
            # KDV, indirimli fiyat üzerinden hesaplanır
            satis_kdv = q((active_sale_price / sale_kdv_factor) * (vat_rate / Decimal("100")))
            
        alis_kdv = q((product_cost / sale_kdv_factor) * (vat_rate / Decimal("100")))

        # 2. Komisyon Hesabı (Komisyon, indirimli satış tutarı üzerinden hesaplanır)
        commission_cost = q(active_sale_price * (commission_rate / Decimal("100")))
        komisyon_kdv = q(commission_cost * Decimal("20") / Decimal("120"))

        # 3. Kargo Hesabı
        kargo_kdv = q((cargo_cost / Decimal("1.20")) * Decimal("0.20"))

        # 4. Mikro İhracat
        intl_service_fee = Decimal("0.00")
        return_loss = Decimal("0.00")
        
        if is_micro_export:
            if is_returned:
                hakedis = active_sale_price - commission_cost
                if active_sale_price <= Decimal("2000.00"):
                    return_loss = q(hakedis * Decimal("0.35"))
                else:
                    return_loss = q(hakedis * Decimal("0.30"))
            else:
                intl_service_fee = q(active_sale_price * Decimal("0.05"))

        # 5. Hizmet Bedeli KDV'si
        hizmet_bedeli_kdv = q(((service_fee + intl_service_fee) / Decimal("1.20")) * Decimal("0.20"))

        # 6. Ödenmesi Gereken Net KDV
        net_kdv = q(satis_kdv - (alis_kdv + komisyon_kdv + kargo_kdv + hizmet_bedeli_kdv))

        # 7. Stopaj
        stopaj = q((active_sale_price / sale_kdv_factor) * Decimal("0.01"))

        # 8. Net Kâr
        net_profit = q(active_sale_price - (product_cost + commission_cost + cargo_cost + service_fee + intl_service_fee + stopaj + net_kdv + return_loss))
        
        # Breakdown Mapping
        breakdown = {
            FinancialTransactionType.PRODUCT_COST.value: product_cost,
            FinancialTransactionType.COMMISSION.value: commission_cost,
            FinancialTransactionType.SHIPPING_FEE.value: cargo_cost,
            FinancialTransactionType.SERVICE_FEE.value: service_fee + intl_service_fee,
            FinancialTransactionType.WITHHOLDING.value: stopaj,
            FinancialTransactionType.VAT_OUTPUT.value: net_kdv,
            FinancialTransactionType.RETURN_LOSS.value: return_loss,
            "DISCOUNT": discount_amount,
        }

        profit_margin = Decimal("0.00")
        if active_sale_price > Decimal("0"):
            profit_margin = q((net_profit / active_sale_price) * Decimal("100.00"))

        profit_on_cost = Decimal("0.00")
        if product_cost > Decimal("0"):
            profit_on_cost = q((net_profit / product_cost) * Decimal("100.00"))

        return {
            "gross_revenue": active_sale_price,  # Artık indirim düşülmüş (Net Satış) hali
            "net_revenue": active_sale_price - (satis_kdv if satis_kdv > 0 else 0),
            "total_costs": q(product_cost + commission_cost + cargo_cost + service_fee + stopaj + net_kdv),
            "net_profit": net_profit,
            "profit_margin": profit_margin,
            "profit_on_cost": profit_on_cost,
            "discount": discount_amount,
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
        sale_price_net = order_item.sale_price_net
        is_micro_export = order_item.order.country_code != "TR"
        is_returned = order_item.order.status in ["Returned", "Cancelled"]
        
        product_cost = Decimal("0.00")
        cargo_cost = Decimal("0.00")
        commission_rate = Decimal("0.00")
        vat_rate = Decimal("10.00")  # Varsayılan %10, ürün bazlı override edilir
        extra_product_cost = Decimal("0.00")
        
        # Transactions'lardan çekebildiğimiz veriler
        for tx in order_item.transactions.all():
            if tx.transaction_type == FinancialTransactionType.PRODUCT_COST.value:
                product_cost = abs(tx.amount)
            elif tx.transaction_type == FinancialTransactionType.SHIPPING_FEE.value:
                cargo_cost = abs(tx.amount)
                
        # Komisyon ve KDV: sipariş satırındaki snapshot verileri öncelikli
        if order_item.applied_commission_rate and order_item.applied_commission_rate > Decimal("0.00"):
            commission_rate = order_item.applied_commission_rate
        if order_item.applied_vat_rate and order_item.applied_vat_rate > Decimal("0.00"):
            vat_rate = order_item.applied_vat_rate

        # Ürün verisi varsa fallback komisyon, vat ve tahmini kargoyu al
        if order_item.product_variant and order_item.product_variant.product:
            variant = order_item.product_variant
            product = variant.product
            
            if commission_rate == Decimal("0.00"):
                commission_rate = product.commission_rate
            if product.vat_rate and product.vat_rate > Decimal("0.00"):
                vat_rate = product.vat_rate
            
            # Variant-level cost overrides Transactions if Transaction isn't present
            if product_cost == Decimal("0.00") and variant.cost_price is not None and variant.cost_price > Decimal("0.00"):
                product_cost = variant.cost_price

            # Ekstra maliyet: cost_price üzerinden yüzde + sabit TL ekle
            extra_product_cost = Decimal("0.00")
            if product_cost > Decimal("0.00"):
                extra_rate = getattr(variant, 'extra_cost_rate', Decimal("0.00")) or Decimal("0.00")
                extra_amount = getattr(variant, 'extra_cost_amount', Decimal("0.00")) or Decimal("0.00")
                extra_product_cost = (product_cost * (extra_rate / Decimal("100"))).quantize(Decimal("0.01")) + extra_amount
                product_cost += extra_product_cost
            
            # Aşama 1 (Tahmini Kargo): Fatura kesilmemişse (Transaction yoksa) desiden hesapla
            if cargo_cost == Decimal("0.00"):
                from core.models import CargoPricing
                
                # Desi önceliği: Varyantta yazan desi, yoksa Üründe yazan desi
                active_desi = variant.desi if variant.desi is not None else product.desi
                
                # Siparişin kendi kargo firması varsa onu kullan, yoksa ürünün varsayılanını kullan
                raw_carrier = order_item.order.cargo_provider_name if order_item.order.cargo_provider_name else product.default_carrier
                
                carrier = _normalize_carrier(raw_carrier)
                
                # TRENDYOL BAREM DESTEK (26 Mart 2026) KONTROLÜ
                # Barem destek tablosu 0-199 ve 200-349 aralıklarını kapsar.
                # 350+ siparişler için 200-349 oranı tahmini olarak kullanılır.
                barem_applied = False
                if active_desi is not None and active_desi <= Decimal("10.00"):
                    # Table seçimi
                    target_table = "table1" if product.fast_delivery else "table2"

                    # Fiyat aralığı: 350+ için 200_349 oranı tahmini kullanılır
                    price_range = "0_199" if sale_price_gross < Decimal("200.00") else "200_349"

                    # Taşıyıcı kontrolü (Eğer tabloda yoksa barem destek uygulanmaz, normal fiyata düşer)
                    if carrier in TRENDYOL_BAREM_RATES.get(target_table, {}).get(price_range, {}):
                        barem_price_kdv_haric = TRENDYOL_BAREM_RATES[target_table][price_range][carrier]
                        cargo_cost = barem_price_kdv_haric * Decimal("1.20")
                        barem_applied = True

                # Barem desteğine uygun değilse veya taşıyıcı listede yoksa normal veritabanından(Excel) çek
                if not barem_applied:
                    try:
                        pricing = CargoPricing.objects.get(carrier_name=carrier, desi=active_desi)
                        # KDV Hariç fiyat üzerine %20 ekleyerek Gross kargo bedeli
                        cargo_cost = pricing.price_without_vat * Decimal("1.20")
                    except CargoPricing.DoesNotExist:
                        cargo_cost = _get_carrier_flat_rate(carrier)

        result = ProfitCalculator.calculate_from_raw(
            sale_price_gross=sale_price_gross,
            product_cost=product_cost,
            cargo_cost=cargo_cost,
            commission_rate=commission_rate,
            vat_rate=vat_rate,
            is_micro_export=is_micro_export,
            sale_price_net=sale_price_net,
            is_returned=is_returned
        )
        result["extra_product_cost"] = extra_product_cost
        return result

    @staticmethod
    def calculate_for_order(order) -> Dict[str, Any]:
        """
        Sipariş bazlı (order-level) kârlılık hesabı.
        Kargo ve hizmet bedeli SİPARİŞ başına bir kez uygulanır — ürün başına değil.
        """
        from decimal import ROUND_HALF_UP
        from core.models import FinancialTransaction, FinancialTransactionType, CargoPricing, CargoInvoice

        def q(val: Decimal) -> Decimal:
            return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        items = list(order.items.all())

        # ── Step 1: Per-item aggregations (komisyon, maliyet, stopaj, kısmi KDV) ──
        total_sale       = Decimal("0")
        sum_product_cost = Decimal("0")
        sum_extra_cost   = Decimal("0")
        sum_commission   = Decimal("0")
        sum_stopaj       = Decimal("0")
        sum_satis_kdv    = Decimal("0")
        sum_alis_kdv     = Decimal("0")
        sum_komisyon_kdv = Decimal("0")

        # Collect order-level context while iterating items
        total_desi   = Decimal("0")
        fast_delivery = False

        for item in items:
            r  = ProfitCalculator.calculate_for_order_item(item)
            bd = r["breakdown"]
            kd = r.get("kdv_detail", {})

            total_sale       += r["gross_revenue"]
            sum_product_cost += bd.get("PRODUCT_COST", Decimal("0"))
            sum_extra_cost   += r.get("extra_product_cost", Decimal("0"))
            sum_commission   += bd.get("COMMISSION", Decimal("0"))
            sum_stopaj       += bd.get("WITHHOLDING", Decimal("0"))
            sum_satis_kdv    += kd.get("satis_kdv", Decimal("0"))
            sum_alis_kdv     += kd.get("alis_kdv", Decimal("0"))
            sum_komisyon_kdv += kd.get("komisyon_kdv", Decimal("0"))

            if item.product_variant:
                desi = item.product_variant.desi
                if desi is None and item.product_variant.product:
                    desi = item.product_variant.product.desi
                if desi:
                    total_desi += desi * item.quantity
                if item.product_variant.product and item.product_variant.product.fast_delivery:
                    fast_delivery = True

        # ── Step 2: Sipariş bazlı kargo (TEK değer) ──
        cargo_source = "estimated"

        # Öncelik 1: CargoInvoice (Trendyol Kargo Faturası API'sinden gerçek tutar)
        from django.db.models import Sum as DjSum
        order_num = str(order.order_number or order.marketplace_order_id or "")
        invoice_total = CargoInvoice.objects.filter(
            organization=order.organization,
            order_number=order_num,
            shipment_package_type="Gönderi Kargo Bedeli",
        ).aggregate(total=DjSum("amount"))["total"]
        # Eğer shipment_package_type filtresiyle sonuç yoksa tüm kayıtları dene
        if not invoice_total:
            invoice_total = CargoInvoice.objects.filter(
                organization=order.organization,
                order_number=order_num,
            ).aggregate(total=DjSum("amount"))["total"]

        if invoice_total and invoice_total > Decimal("0"):
            order_cargo  = q(invoice_total)
            cargo_source = "invoice"
        else:
            # Öncelik 2: FinancialTransaction.SHIPPING_FEE
            shipping_tx = FinancialTransaction.objects.filter(
                order_item_ref__order=order,
                transaction_type=FinancialTransactionType.SHIPPING_FEE.value
            ).order_by('-occurred_at').first()

            if shipping_tx and shipping_tx.amount > Decimal("0"):
                order_cargo  = shipping_tx.amount
                cargo_source = "transaction"
                cargo_source = "transaction"
            else:
                # Öncelik 3: Desi × birim_fiyat tahmini (fallback)
                raw_carrier = order.cargo_provider_name or ""
                if not raw_carrier and items:
                    first = items[0]
                    if first.product_variant and first.product_variant.product:
                        raw_carrier = first.product_variant.product.default_carrier or ""
                carrier = _normalize_carrier(raw_carrier)

                # Gerçek fatura flat tarife — barem/CargoPricing bu seller için geçerli değil.
                # CarrierFlatRate DB'den okur; kayıt yoksa FALLBACK dict'e düşer.
                order_cargo  = _get_carrier_flat_rate(carrier)
                cargo_source = "estimated"

        # ── Step 3: Sipariş bazlı hizmet bedeli (TEK değer) ──
        service_tx = FinancialTransaction.objects.filter(
            order_item_ref__order=order,
            transaction_type=FinancialTransactionType.SERVICE_FEE.value
        ).first()
        order_service_fee = service_tx.amount if (service_tx and service_tx.amount > Decimal("0")) else Decimal("13.19")

        # ── Step 4: KDV hesabı ──
        kargo_kdv  = q(order_cargo * Decimal("20") / Decimal("120"))
        hizmet_kdv = q(order_service_fee * Decimal("20") / Decimal("120"))
        net_kdv    = q(sum_satis_kdv - sum_alis_kdv - sum_komisyon_kdv - kargo_kdv - hizmet_kdv)

        # ── Step 5: Net Kâr ──
        net_profit = q(total_sale - sum_product_cost - sum_commission - order_cargo - order_service_fee - sum_stopaj - net_kdv)

        profit_margin  = q((net_profit / total_sale) * Decimal("100")) if total_sale > Decimal("0") else Decimal("0")
        profit_on_cost = q((net_profit / sum_product_cost) * Decimal("100")) if sum_product_cost > Decimal("0") else Decimal("0")

        return {
            "total_sale":         total_sale,
            "product_cost":       sum_product_cost,
            "extra_product_cost": sum_extra_cost,
            "commission":         sum_commission,
            "cargo":              order_cargo,
            "cargo_source":       cargo_source,  # "invoice" | "transaction" | "estimated"
            "service_fee":        order_service_fee,
            "withholding":        sum_stopaj,
            "net_profit":         net_profit,
            "profit_margin":      profit_margin,
            "profit_on_cost":     profit_on_cost,
            "kdv_detail": {
                "satis_kdv":        q(sum_satis_kdv),
                "alis_kdv":         q(sum_alis_kdv),
                "kargo_kdv":        kargo_kdv,
                "komisyon_kdv":     q(sum_komisyon_kdv),
                "hizmet_bedeli_kdv": hizmet_kdv,
                "net_kdv":          net_kdv,
            },
        }
