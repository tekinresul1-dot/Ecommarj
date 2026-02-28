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

        # Organizasyonun siparişlerini çek
        orders_qs = Order.objects.select_related("marketplace_account").filter(
            organization=org, channel=channel
        )

        if countries:
            country_list = [c.strip() for c in countries.split(",")]
            orders_qs = orders_qs.filter(country_code__in=country_list)

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
        
        products = Product.objects.filter(organization=org).order_by('-created_at')
        
        # Simple serialization
        data = []
        for p in products:
            data.append({
                "id": p.id,
                "title": p.title,
                "barcode": p.barcode,
                "marketplace_sku": p.marketplace_sku,
                "sale_price": str(p.sale_price),
                "vat_rate": str(p.vat_rate),
                "commission_rate": str(p.commission_rate),
                "image_url": p.image_url,
                "is_active": p.is_active
            })

        return Response({
            "count": len(data),
            "results": data
        })
