from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from decimal import Decimal

from core.models import Order, OrderItem, MarketplaceAccount, FinancialTransactionType
from core.services.profit_calculator import ProfitCalculator
from core.tasks import sync_all_trendyol_data_task

class TriggerSyncView(APIView):
    """
    Dashboard'dan manuel "Trendyol Senkronize Et" butonuna basıldığında tetiklenir.
    Kullanıcının Trendyol hesaplarını bulup Celery task'ine gönderir.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # Auto-create profile and org if missing (useful for superusers or first time testing)
        from core.models import UserProfile, Organization
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        if not org:
            org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
            profile.organization = org
            profile.save()
            
        accounts = MarketplaceAccount.objects.filter(organization=org, channel=MarketplaceAccount.Channel.TRENDYOL, is_active=True)
        
        if not accounts.exists():
            return Response({"error": "Aktif bir Trendyol API hesabı bulunamadı."}, status=404)
            
        for acc in accounts:
            try:
                # Run synchronously for MVP/Testing instead of celery
                sync_all_trendyol_data_task(str(acc.id))
            except ValueError as e:
                return Response({"error": str(e)}, status=400)
            except Exception as e:
                return Response({"error": f"Senkronizasyon sırasında hata oluştu: {str(e)}"}, status=500)
            
        return Response({"message": f"{accounts.count()} hesap için senkronizasyon başarıyla tamamlandı."})

class DashboardOverviewView(APIView):
    """
    GET /api/dashboard/overview
    Filtrelere göre Sipariş, Ürün ve Finansal verileri toplayıp gerçek KPI döndürür.
    Mikro ihracat ve Trendyol olarak 'channel' parametresiyle çalışır.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from core.models import UserProfile, Organization
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        if not org:
            org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
            profile.organization = org
            profile.save()

        # Filtreleri al
        channel = request.query_params.get("channel", "trendyol")
        countries = request.query_params.get("countries", "") # virgülle ayrılmış
        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")

        # Organizasyonun siparişlerini çek
        orders_qs = Order.objects.select_related("marketplace_account").filter(
            organization=org, channel=channel
        )

        if countries:
            country_list = [c.strip() for c in countries.split(",")]
            orders_qs = orders_qs.filter(country_code__in=country_list)

        if min_date_str and max_date_str:
            from datetime import datetime, time
            try:
                min_date = timezone.make_aware(datetime.strptime(min_date_str, "%Y-%m-%d"))
                max_date = timezone.make_aware(datetime.combine(datetime.strptime(max_date_str, "%Y-%m-%d"), time.max))
                orders_qs = orders_qs.filter(order_date__gte=min_date, order_date__lte=max_date)
            except ValueError:
                pass # Parse error, apply no date filter

        total_orders = orders_qs.count()
        order_items = OrderItem.objects.select_related("order").prefetch_related("transactions").filter(order__in=orders_qs)

        total_gross = Decimal("0.00")
        total_net = Decimal("0.00")
        total_costs = Decimal("0.00")
        total_profit = Decimal("0.00")
        
        breakdown = {tx_type.value: Decimal("0.00") for tx_type in FinancialTransactionType}
        country_profits = {}
        
        # Ek Metrik Havuzları (Rakip UI için)
        total_items_sold = 0
        total_cargo_cost = Decimal("0.00")
        total_commission_cost = Decimal("0.00")
        total_discount = Decimal("0.00")
        
        # Funnel için Toplamlar (Brüt Ciro -> Kargo Düşülmüş -> Pazaryeri Masrafı Düşülmüş -> Vergi Düşülmüş -> Net)
        funnel_gross = Decimal("0.00")
        funnel_cargo = Decimal("0.00")
        funnel_marketplace_fees = Decimal("0.00") # Komisyon + Hizmet bedeli + Ceza vs
        funnel_taxes = Decimal("0.00")            # Satış KDV + Stopaj
        funnel_net = Decimal("0.00")

        # Profit motoruyla her satırı tek tek hesapla
        for item in order_items:
            res = ProfitCalculator.calculate_for_order_item(item)
            
            gross = res["gross_revenue"]
            net = res["net_revenue"]
            costs = res["total_costs"]
            profit = res["net_profit"]
            
            total_gross += gross
            total_net += net
            total_costs += costs
            total_profit += profit
            total_items_sold += item.quantity
            total_discount += item.discount
            
            funnel_gross += gross
            
            item_cargo = Decimal("0.00")
            item_mp_fees = Decimal("0.00")
            item_taxes = Decimal("0.00")
            
            for k, v in res["breakdown"].items():
                breakdown[k] += v
                if k == FinancialTransactionType.SHIPPING_FEE.value:
                    item_cargo += v
                    total_cargo_cost += v
                elif k == FinancialTransactionType.COMMISSION.value:
                    item_mp_fees += v
                    total_commission_cost += v
                elif k in [FinancialTransactionType.SERVICE_FEE.value, FinancialTransactionType.PENALTY.value]:
                    item_mp_fees += v
                elif k in [FinancialTransactionType.VAT_OUTPUT.value, FinancialTransactionType.WITHHOLDING.value]:
                    item_taxes += v
            
            funnel_cargo += item_cargo
            funnel_marketplace_fees += item_mp_fees
            funnel_taxes += item_taxes
            
            c_code = item.order.country_code
            country_profits[c_code] = country_profits.get(c_code, Decimal("0.00")) + profit

        funnel_net = total_profit

        # Kâr Marjları ve Oranlar
        profit_margin = Decimal("0.00")
        if total_net > Decimal("0.00"):
            profit_margin = (total_profit / total_net) * Decimal("100.00")
            
        profit_on_cost_ratio = Decimal("0.00")
        total_product_cost = breakdown.get(FinancialTransactionType.PRODUCT_COST.value, Decimal("0.00"))
        if total_product_cost > Decimal("0.00"):
            profit_on_cost_ratio = (total_profit / total_product_cost) * Decimal("100.00")

        # Kayıp Kaçak (Ceza + İade + Erken Ödeme)
        lost_and_leakage = (
            breakdown.get(FinancialTransactionType.PENALTY.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.RETURN_LOSS.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.EARLY_PAYMENT.value, Decimal("0"))
        )
        
        # --- Ek: Metrik Listeleri (Sipariş, Ürün, İade vs) ---
        
        # Sipariş Metrikleri
        order_metrics = {
            "order_count": total_orders,
            "avg_revenue_per_order": str(round(total_net / total_orders, 2)) if total_orders > 0 else "0.00",
            "avg_profit_per_order": str(round(total_profit / total_orders, 2)) if total_orders > 0 else "0.00",
            "avg_cargo_per_order": str(round(total_cargo_cost / total_orders, 2)) if total_orders > 0 else "0.00",
        }
        
        # Ürün Metrikleri
        product_metrics = {
            "items_sold": total_items_sold,
            "avg_revenue_per_item": str(round(total_net / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_profit_per_item": str(round(total_profit / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_cargo_per_item": str(round(total_cargo_cost / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_commission_rate": str(round((total_commission_cost / total_gross)*100, 2)) if total_gross > 0 else "0.00",
            "avg_discount_rate": str(round((total_discount / total_gross)*100, 2)) if total_gross > 0 else "0.00",
        }
        
        # İade Metrikleri (Şimdilik mock veya iade tutarlarından)
        return_loss_val = breakdown.get(FinancialTransactionType.RETURN_LOSS.value, Decimal("0.00"))
        return_metrics = {
            "return_rate": "12.5", # Mock - Sipariş durumuna göre yapılmalı
            "total_return_cost": str(return_loss_val),
            "return_cargo_loss": str(round(return_loss_val * Decimal("0.6"), 2)), # Örnek kargo yansıması
            "overseas_operation_fee": "0.00"
        }
        
        # Reklam Metrikleri
        ads_val = breakdown.get(FinancialTransactionType.ADS_COST.value, Decimal("0.00"))
        ads_metrics = {
            "total_ads_cost": str(ads_val),
            "influencer_cut": "0.00",
            "ads_profit_index": str(round((ads_val / total_profit)*100, 2)) if total_profit > 0 else "0.00",
            "ads_revenue_index": str(round((ads_val / total_net)*100, 2)) if total_net > 0 else "0.00",
        }
        
        # Net Kâr Performansı Hunisi (Funnel)
        net_profit_funnel = [
            {"name": "Ciro", "value": str(funnel_gross)},
            {"name": "Kargo Düşülmüş", "value": str(funnel_gross - funnel_cargo)},
            {"name": "Pazaryeri Masrafı Düşülmüş", "value": str(funnel_gross - funnel_cargo - funnel_marketplace_fees)},
            {"name": "Vergi Düşülmüş", "value": str(funnel_gross - funnel_cargo - funnel_marketplace_fees - funnel_taxes)},
            {"name": "Kâr", "value": str(funnel_net)},
        ]
        
        # Geçici Kâr Performansı History (Area Chart için)
        from datetime import timedelta
        history = []
        for i in range(5, -1, -1):
            history.append({
                "date": (timezone.now() - timedelta(days=i)).strftime("%d %b"),
                "profit": str(round(total_profit / 6 + Decimal(i * 10), 2)) # Mock trend distribution
            })

        # Kritik Stok Uyarıları
        from core.models import Product
        org_products = Product.objects.filter(organization=org, is_active=True)
        low_stock_list = []
        for p in org_products:
            if p.is_low_stock:
                low_stock_list.append({
                    "id": p.id,
                    "title": p.title,
                    "barcode": p.barcode,
                    "current_stock": p.current_stock,
                    "initial_stock": p.initial_stock,
                    "image_url": p.image_url
                })
        
        # En az stoğu kalanı en üste al, max 5 tane yolla
        low_stock_list = sorted(low_stock_list, key=lambda x: x["current_stock"])[:5]

        return Response({
            "kpis": {
                "total_orders": total_orders,
                "gross_revenue": str(total_gross),
                "net_revenue": str(total_net),
                "total_costs": str(total_costs),
                "net_profit": str(total_profit),
                "profit_margin": str(round(profit_margin, 2)),
                "profit_on_cost_ratio": str(round(profit_on_cost_ratio, 2)),
                "lost_and_leakage": str(lost_and_leakage),
            },
            "profit_breakdown": {k: str(v) for k, v in breakdown.items()},
            "country_profit": [{"country": k, "profit": str(v)} for k, v in country_profits.items()],
            "order_metrics": order_metrics,
            "product_metrics": product_metrics,
            "return_metrics": return_metrics,
            "ads_metrics": ads_metrics,
            "net_profit_funnel": net_profit_funnel,
            "profit_performance_history": history,
            "low_stock_alerts": low_stock_list,
        })


class MockReportsView(APIView):
    """
    Diğer listeleme sayfaları için geçici endpoint (UI'ın çalışması adına boş veya mock liste döner)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, report_type):
        return Response({
            "report_type": report_type,
            "data": []
        })


class TrendyolTestConnectionView(APIView):
    """
    POST /api/integrations/trendyol/test-connection/
    Trendyol bağlantısını test eder (1 ürün çekmeye çalışır).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        api_key = request.data.get("api_key", "").strip()
        api_secret = request.data.get("api_secret", "").strip()
        supplier_id = request.data.get("supplier_id", "").strip()

        if not all([api_key, api_secret, supplier_id]):
            return Response({"ok": False, "message": "Eksik bilgi: api_key, api_secret veya supplier_id gerekli."}, status=400)

        import requests
        url = f"https://api.trendyol.com/sapigw/suppliers/{supplier_id}/products"
        params = {"approved": "true", "page": 0, "size": 1}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        try:
            res = requests.get(url, auth=(api_key, api_secret), params=params, headers=headers, timeout=30)
            
            if not res.ok:
                text = res.text
                status = res.status_code
                message = text[:300]
                
                # HTML check
                if '<html' in text.lower() or 'cloudflare' in text.lower():
                    message = "Trendyol API erişiminiz engellendi. Girdiğiniz bilgiler hatalı olabilir veya geçici bir kesinti yaşanıyor."
                elif status == 401:
                    message = "API Key veya API Secret hatalı. Lütfen kontrol edip tekrar deneyin."
                elif status == 403:
                    message = "Bu Satıcı ID (Supplier ID) için yetkiniz yok veya bilgiler eşleşmiyor."
                elif status == 429:
                    message = "Rate limit, tekrar dene"
                else:
                    try:
                        data = res.json()
                        message = data.get("message", text[:300])
                    except ValueError:
                        pass
                
                return Response({
                    "ok": False,
                    "code": status,
                    "message": message,
                    "status": res.status_code,
                    "raw_head": dict(res.headers)
                }, status=400)
                
            data = res.json()
            return Response({
                "ok": True,
                "sample_product_count_hint": data.get("totalElements", 0),
                "request_id": res.headers.get("x-request-id", "unknown")
            })
            
        except requests.RequestException as e:
            return Response({"ok": False, "message": f"Bağlantı hatası: {str(e)}", "code": 500}, status=500)


class TrendyolSaveCredentialsView(APIView):
    """
    POST /api/integrations/trendyol/save-credentials/
    Kullanıcının Trendyol API Key, Secret ve Satıcı ID'sini veritabanına şifreli kaydeder.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from core.models import UserProfile, Organization
        from core.utils.encryption import decrypt_value
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        if not org:
            org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
            profile.organization = org
            profile.save()
            
        account = MarketplaceAccount.objects.filter(
            organization=org, 
            channel=MarketplaceAccount.Channel.TRENDYOL
        ).first()

        if not account:
            return Response({
                "api_key": "",
                "api_secret": "",
                "supplier_id": ""
            })

        return Response({
            "api_key": account.api_key,
            "api_secret": decrypt_value(account.api_secret), 
            "supplier_id": account.seller_id
        })

    def post(self, request):
        user = request.user
        from core.models import UserProfile, Organization
        from core.utils.encryption import encrypt_value
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        if not org:
            org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
            profile.organization = org
            profile.save()

        api_key = request.data.get("api_key", "").strip()
        api_secret = request.data.get("api_secret", "").strip()
        supplier_id = request.data.get("supplier_id", "").strip()

        if not supplier_id:
            return Response({"error": "Satıcı ID (Supplier ID) zorunludur."}, status=400)

        account, created = MarketplaceAccount.objects.update_or_create(
            organization=org,
            channel=MarketplaceAccount.Channel.TRENDYOL,
            defaults={
                "store_name": f"Trendyol Store - {supplier_id}",
                "seller_id": supplier_id,
                "api_key": api_key,
                "api_secret": encrypt_value(api_secret),
                "is_active": True
            }
        )

        auto_sync = request.data.get("auto_sync", True)
        if auto_sync and account.api_key and account.api_secret:
            try:
                sync_all_trendyol_data_task(str(account.id))
            except ValueError as e:
                # Silmiyoruz, kullanıcı Settings sayfasında düzeltip tekrar test bağlantısı atabilir
                return Response({"error": str(e)}, status=400)
            except Exception as e:
                return Response({"error": f"Veriler senkronize edilemedi. Hata: {str(e)}"}, status=500)

        return Response({"message": "Trendyol API bilgileri başarıyla kaydedildi.", "sync_started": auto_sync})


class ProductListView(APIView):
    """
    GET /api/products/
    Veritabanına (Trendyol üzerinden) senkronize edilmiş ürünlerin tablo olarak dökümünü sağlar.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from core.models import UserProfile, Organization
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        if not org:
            org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
            profile.organization = org
            profile.save()

        from core.models import Product
        
        products = Product.objects.filter(organization=org).prefetch_related('variants').order_by('-created_at')
        
        # Simple serialization
        data = []
        for p in products:
            product_data = {
                "id": p.id,
                "title": p.title,
                "barcode": p.barcode,
                "marketplace_sku": p.marketplace_sku,
                "sale_price": str(p.sale_price),
                "vat_rate": str(p.vat_rate),
                "commission_rate": str(p.commission_rate),
                "image_url": p.image_url,
                "desi": str(p.desi),
                "default_carrier": p.default_carrier,
                "brand": p.brand,
                "return_rate": str(p.return_rate),
                "fast_delivery": p.fast_delivery,
                "is_active": p.is_active,
                "variants": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "barcode": v.barcode,
                        "cost_price": str(v.cost_price),
                        "cost_vat_rate": str(v.cost_vat_rate),
                        "desi": str(v.desi) if v.desi is not None else None
                    } for v in p.variants.all()
                ]
            }
            data.append(product_data)

        return Response({
            "count": len(data),
            "results": data
        })

    def patch(self, request):
        """
        Updates product fields like desi and default_carrier, or variant fields like cost_price.
        Expects payload: 
        { "id": 123, "desi": "1.50", "default_carrier": "Aras Kargo" } -> Product update
        { "variant_id": 456, "cost_price": "250.00", "cost_vat_rate": "10", "desi": "0.5" } -> Variant update
        """
        user = request.user
        from core.models import UserProfile, Organization, Product, ProductVariant
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        
        variant_id = request.data.get("variant_id")
        
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product__organization=org)
            except ProductVariant.DoesNotExist:
                return Response({"error": "Variant not found"}, status=404)
                
            if "cost_price" in request.data:
                variant.cost_price = Decimal(str(request.data["cost_price"]))
            if "cost_vat_rate" in request.data:
                variant.cost_vat_rate = Decimal(str(request.data["cost_vat_rate"]))
            if "desi" in request.data:
                if request.data["desi"] is None or request.data["desi"] == "":
                    variant.desi = None
                else:
                    variant.desi = Decimal(str(request.data["desi"]))
                    
            variant.save()
            return Response({
                "message": "Varyant güncellendi.",
                "variant_id": variant.id,
                "cost_price": str(variant.cost_price),
                "cost_vat_rate": str(variant.cost_vat_rate),
                "desi": str(variant.desi) if variant.desi is not None else None
            })
            
        else:
            product_id = request.data.get("id")
            if not product_id:
                 return Response({"error": "Product ID or Variant ID is required"}, status=400)
                 
            try:
                product = Product.objects.get(id=product_id, organization=org)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=404)
                
            if "desi" in request.data:
                try:
                    product.desi = Decimal(str(request.data["desi"]))
                except Exception:
                    return Response({"error": "Invalid desi format"}, status=400)
                    
            if "default_carrier" in request.data:
                product.default_carrier = str(request.data["default_carrier"])
                
            if "return_rate" in request.data:
                try:
                    product.return_rate = Decimal(str(request.data["return_rate"]))
                except Exception:
                    return Response({"error": "Invalid return_rate format"}, status=400)
                    
            if "fast_delivery" in request.data:
                product.fast_delivery = bool(request.data["fast_delivery"])
                
            product.save()
            
            return Response({
                "id": product.id,
                "desi": str(product.desi),
                "default_carrier": product.default_carrier,
                "return_rate": str(product.return_rate),
                "fast_delivery": product.fast_delivery,
                "message": "Ürün güncellendi."
            })

class OrderListView(APIView):
    """
    GET /api/orders/
    Sipariş listesini ve her siparişin detaylı kârlılık dökümünü döner.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.userprofile
            org = profile.organization
        except Exception:
            return Response({"error": "Organizasyon bulunamadı"}, status=400)

        from core.models import Order
        from core.services.profit_calculator import ProfitCalculator
        from decimal import Decimal
        
        # Sadece bu organizasyona ait olan siparişleri getir
        # prefetch_related ile db call optimizasyonu
        orders = Order.objects.filter(marketplace_account__organization=org).prefetch_related('items__product_variant__product', 'items__transactions').order_by('-order_date')
        
        # Sadece son 50 siparişi gönderelim
        orders = orders[:50]

        data = []
        for order in orders:
            total_gross = Decimal("0.00")
            total_net_profit = Decimal("0.00")
            
            items_data = []
            
            cum_breakdown = {
                "product_cost": Decimal("0.00"),
                "commission": Decimal("0.00"),
                "shipping_fee": Decimal("0.00"),
                "service_fee": Decimal("0.00"),
                "withholding": Decimal("0.00"),
                "net_kdv": Decimal("0.00"),
                "satis_kdv": Decimal("0.00"),
                "alis_kdv": Decimal("0.00"),
                "kargo_kdv": Decimal("0.00"),
                "komisyon_kdv": Decimal("0.00"),
                "hizmet_bedeli_kdv": Decimal("0.00"),
            }

            for item in order.items.all():
                profit_info = ProfitCalculator.calculate_for_order_item(item)
                
                total_gross += profit_info["gross_revenue"]
                total_net_profit += profit_info["net_profit"]
                
                bd = profit_info["breakdown"]
                cum_breakdown["product_cost"] += bd.get("PRODUCT_COST", Decimal("0.00"))
                cum_breakdown["commission"] += bd.get("COMMISSION", Decimal("0.00"))
                cum_breakdown["shipping_fee"] += bd.get("SHIPPING_FEE", Decimal("0.00"))
                cum_breakdown["service_fee"] += bd.get("SERVICE_FEE", Decimal("0.00"))
                cum_breakdown["withholding"] += bd.get("WITHHOLDING", Decimal("0.00"))
                
                kdv = profit_info.get("kdv_detail", {})
                cum_breakdown["net_kdv"] += kdv.get("net_kdv", Decimal("0.00"))
                cum_breakdown["satis_kdv"] += kdv.get("satis_kdv", Decimal("0.00"))
                cum_breakdown["alis_kdv"] += kdv.get("alis_kdv", Decimal("0.00"))
                cum_breakdown["kargo_kdv"] += kdv.get("kargo_kdv", Decimal("0.00"))
                cum_breakdown["komisyon_kdv"] += kdv.get("komisyon_kdv", Decimal("0.00"))
                cum_breakdown["hizmet_bedeli_kdv"] += kdv.get("hizmet_bedeli_kdv", Decimal("0.00"))
                
                title = "Bilinmeyen Ürün"
                barcode = item.sku
                commission_rate = Decimal("0.00")
                if item.product_variant and item.product_variant.product:
                    title = item.product_variant.product.title
                    barcode = item.product_variant.barcode
                    commission_rate = item.product_variant.product.commission_rate
                
                items_data.append({
                    "id": item.id,
                    "title": title,
                    "barcode": barcode,
                    "quantity": item.quantity,
                    "sale_price_gross": str(item.sale_price_gross),
                    "commission_rate": str(commission_rate),
                    "profit": profit_info
                })
                
            profit_margin = Decimal("0.00")
            if total_gross > Decimal("0.00"):
                profit_margin = round((total_net_profit / total_gross) * Decimal("100.00"), 2)
                
            profit_on_cost = Decimal("0.00")
            if cum_breakdown["product_cost"] > Decimal("0.00"):
                profit_on_cost = round((total_net_profit / cum_breakdown["product_cost"]) * Decimal("100.00"), 2)

            data.append({
                "id": order.id,
                "order_number": order.marketplace_order_id,
                "order_date": order.order_date.strftime("%d %b %Y - %H:%M") if order.order_date else "",
                "status": order.status,
                "total_gross": str(total_gross),
                "total_profit": str(total_net_profit),
                "profit_margin": str(profit_margin),
                "profit_on_cost": str(profit_on_cost),
                "items": items_data,
                "aggregated_breakdown": {k: str(v) for k, v in cum_breakdown.items()}
            })

        return Response({"ok": True, "data": data})

class ProductAnalysisView(APIView):
    """
    GET /api/reports/product-analysis/
    Ürün bazlı (barkod/varyant) kârlılık verilerini döndürür.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            org = profile.organization
        except Exception as e:
            return Response({"error": f"Organizasyon bulunamadı: {str(e)}"}, status=400)

        from core.models import OrderItem, Order
        from core.services.profit_calculator import ProfitCalculator
        from decimal import Decimal

        orders = Order.objects.filter(marketplace_account__organization=org)
        
        items = OrderItem.objects.filter(
            order__in=orders,
            product_variant__isnull=False
        ).select_related('product_variant', 'product_variant__product', 'order').prefetch_related('transactions')

        analysis_map = {}

        for item in items:
            variant = item.product_variant
            if not variant or not variant.product:
                continue

            barcode = variant.barcode or ""
            if not barcode:
                continue

            if barcode not in analysis_map:
                analysis_map[barcode] = {
                    "barcode": barcode,
                    "title": variant.product.title,
                    "stock": variant.stock,
                    "model_code": variant.product.model_code or "",
                    "category": variant.product.category or "",
                    "total_sold_quantity": 0,
                    "total_sales_amount": Decimal("0.00"),
                    "total_profit": Decimal("0.00"),
                    "total_cost": Decimal("0.00"),
                    "return_cargo_loss": Decimal("0.00"),
                }

            qty = item.quantity
            is_returned = item.order.status.lower() in ["returned", "iade edildi", "cancelled", "iptal edildi"]
            
            # Gross profit calc
            profit_info = ProfitCalculator.calculate_for_order_item(item)
            
            if not is_returned:
                analysis_map[barcode]["total_sold_quantity"] += qty
                analysis_map[barcode]["total_sales_amount"] += profit_info["gross_revenue"]
                analysis_map[barcode]["total_profit"] += profit_info["net_profit"]
                
                # Approximate cost = sum of PRODUCT_COST in breakdown
                bd = profit_info.get("breakdown", {})
                analysis_map[barcode]["total_cost"] += bd.get("PRODUCT_COST", Decimal("0.00"))
            else:
                # If returned, usually you lose the shipping fee out and back.
                # Assuming 2x one-way shipping as standard return loss proxy, or just 1x depending on market logic.
                bd = profit_info.get("breakdown", {})
                shipping = bd.get("SHIPPING_FEE", Decimal("0.00"))
                shipping_kdv = profit_info.get("kdv_detail", {}).get("kargo_kdv", Decimal("0.00"))
                analysis_map[barcode]["return_cargo_loss"] += (shipping + shipping_kdv)

        data = []
        for barcode, stats in analysis_map.items():
            profit_margin = Decimal("0.00")
            profit_rate = Decimal("0.00") 
            
            total_sales = stats["total_sales_amount"]
            total_profit = stats["total_profit"]
            total_cost = stats["total_cost"]

            if total_sales > Decimal("0.00"):
                profit_margin = round((total_profit / total_sales) * Decimal("100.00"), 2)
                
            if total_cost > Decimal("0.00"):
                profit_rate = round((total_profit / total_cost) * Decimal("100.00"), 2)
            
            data.append({
                "id": barcode, # Use barcode as unique id for react key
                "barcode": stats["barcode"],
                "title": stats["title"],
                "stock": stats["stock"],
                "model_code": stats["model_code"],
                "category": stats["category"],
                "total_sold_quantity": stats["total_sold_quantity"],
                "total_sales_amount": str(stats["total_sales_amount"]),
                "total_profit": str(stats["total_profit"]),
                "return_cargo_loss": str(stats["return_cargo_loss"]),
                "profit_margin": str(profit_margin),
                "profit_rate": str(profit_rate),
            })

        # Sort by total sales amount desc
        data.sort(key=lambda x: Decimal(x["total_sales_amount"]), reverse=True)

        return Response({"ok": True, "data": data})
