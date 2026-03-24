from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import models as django_models
from decimal import Decimal

from core.models import (
    Organization, MarketplaceAccount, Product, ProductVariant,
    Order, OrderItem, FinancialTransactionType
)
from core.utils.mixins import TenantQuerySetMixin
from core.services.profit_calculator import ProfitCalculator
from core.tasks import sync_all_trendyol_data_task

MONTHS_TR = {
    1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 
    7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"
}

def format_date_tr(dt):
    if not dt:
        return ""
    from django.utils import timezone
    from datetime import datetime
    if isinstance(dt, datetime) and timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return f"{dt.day:02d} {MONTHS_TR[dt.month]} {dt.year} - {dt.strftime('%H:%M') if isinstance(dt, datetime) else '00:00'}"

def format_date_short_tr(dt):
    if not dt:
        return ""
    from django.utils import timezone
    from datetime import datetime
    if isinstance(dt, datetime) and timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return f"{dt.day:02d} {MONTHS_TR[dt.month]}"
    
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


class ProductStockSyncView(APIView):
    """
    POST /api/products/sync-stock/
    Sadece ürün stok bilgilerini Trendyol'dan çeker ve günceller (sipariş/hakediş senkronizasyonu yapmaz).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from core.models import UserProfile
        from core.services.sync_service import TrendyolSyncService
        from core.utils.encryption import decrypt_value

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        org = profile.organization
        if not org:
            return Response({"error": "Organizasyon bulunamadı."}, status=404)

        accounts = MarketplaceAccount.objects.filter(
            organization=org,
            channel=MarketplaceAccount.Channel.TRENDYOL,
            is_active=True
        )
        if not accounts.exists():
            return Response({"error": "Aktif bir Trendyol API hesabı bulunamadı. Lütfen Ayarlar > Trendyol bölümünden API kimlik bilgilerinizi ekleyin."}, status=404)

        synced_count = 0
        for acc in accounts:
            try:
                service = TrendyolSyncService(acc)
                service.sync_products()
                synced_count += 1
            except ValueError as e:
                return Response({"error": str(e)}, status=400)
            except Exception as e:
                return Response({"error": f"Stok senkronizasyonu sırasında hata oluştu: {str(e)}"}, status=500)

        return Response({"message": f"Stok bilgileri güncellendi. {synced_count} Trendyol hesabı senkronize edildi."})


class DashboardOverviewView(APIView):
    """
    GET /api/dashboard/overview
    Filtrelere göre Sipariş, Ürün ve Finansal verileri toplayıp gerçek KPI döndürür.
    
    Toplam Ciro = Sipariş kayıtlarındaki sale_price_net toplamı (Trendyol'un "amount" alanı — indirimli satış fiyatı)
    Maliyetlendirilen Ciro = Sadece maliyeti tanımlı ürünlerin cirosu
    Kâr Tutarı = Maliyetlendirilen ciro üzerinden ProfitCalculator ile hesaplanan kâr
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from core.models import UserProfile, Organization
        from datetime import datetime as dt_cls, time as dt_time, timezone as dt_tz
        from collections import defaultdict
        
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        if not org:
            org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
            profile.organization = org
            profile.save()

        # Filtreleri al
        channel = request.query_params.get("channel", "trendyol")
        countries = request.query_params.get("countries", "")
        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")

        # Organizasyonun siparişlerini çek
        # Trendyol panelinde domestic ve micro_export birlikte gösteriliyor
        if channel == "trendyol":
            orders_qs = Order.objects.select_related("marketplace_account").filter(
                organization=org, channel__in=["trendyol", "micro_export"]
            )
        else:
            orders_qs = Order.objects.select_related("marketplace_account").filter(
                organization=org, channel=channel
            )

        if countries:
            country_list = [c.strip() for c in countries.split(",")]
            orders_qs = orders_qs.filter(country_code__in=country_list)

        if min_date_str and max_date_str:
            try:
                min_date = dt_cls.strptime(min_date_str, "%Y-%m-%d").replace(tzinfo=dt_tz.utc)
                max_date = dt_cls.combine(
                    dt_cls.strptime(max_date_str, "%Y-%m-%d"), dt_time.max
                ).replace(tzinfo=dt_tz.utc)
                orders_qs = orders_qs.filter(order_date__gte=min_date, order_date__lte=max_date)
            except ValueError:
                pass

        # ---------------------------------------------------------------
        # 1. TOPLAM CİRO = Direkt sipariş kayıtlarından (Trendyol gibi)
        #    - Tüm siparişlerin "sale_price_net" (indirimli satış tutarı) toplamı
        #    - İptal ve iade düşülmüş hali (aktif siparişler)
        # ---------------------------------------------------------------
        total_orders = orders_qs.count()
        
        active_orders_qs = orders_qs.exclude(status__in=["Cancelled", "Returned", "UnSupplied"])
        cancelled_orders_qs = orders_qs.filter(status__in=["Cancelled", "Returned"])
        
        active_order_count = active_orders_qs.count()
        cancelled_count = cancelled_orders_qs.count()
        
        # Toplam Ciro: Aktif sipariş kalemlerinin sale_price_net toplamı
        # sale_price_net = Trendyol'un "amount" alanı (indirimli satış tutarı)
        active_items_qs = OrderItem.objects.filter(
            order__in=active_orders_qs
        ).exclude(status__in=["Cancelled", "Returned", "UnSupplied"])
        
        revenue_agg = active_items_qs.aggregate(
            total_gross=django_models.Sum("sale_price_gross"),
            total_net=django_models.Sum("sale_price_net"),
            total_discount=django_models.Sum("discount"),
            total_items=django_models.Count("id"),
            total_quantity=django_models.Sum("quantity"),
        )
        
        toplam_ciro = revenue_agg["total_net"] or Decimal("0.00")
        total_gross = revenue_agg["total_gross"] or Decimal("0.00")
        total_discount = revenue_agg["total_discount"] or Decimal("0.00")
        total_items_sold = revenue_agg["total_quantity"] or 0
        
        # ---------------------------------------------------------------
        # 2. KARLILIK HESABI = ProfitCalculator ile (sadece maliyeti olan ürünler)
        # ---------------------------------------------------------------
        total_costs = Decimal("0.00")
        total_profit = Decimal("0.00")
        total_costed_revenue = Decimal("0.00")
        
        breakdown = defaultdict(Decimal)
        for tx_type in FinancialTransactionType:
            breakdown[tx_type.value] = Decimal("0.00")
        country_profits = {}
        
        total_cargo_cost = Decimal("0.00")
        total_commission_cost = Decimal("0.00")
        
        funnel_gross = Decimal("0.00")
        funnel_cargo = Decimal("0.00")
        funnel_marketplace_fees = Decimal("0.00")
        funnel_taxes = Decimal("0.00")
        funnel_net = Decimal("0.00")

        # ProfitCalculator ile her satırı tek tek hesapla
        for item in active_items_qs.select_related("order").prefetch_related("transactions"):
            res = ProfitCalculator.calculate_for_order_item(item)
            
            item_revenue = res["gross_revenue"]  # ProfitCalculator'ın döndüğü = sale_price_net
            costs = res["total_costs"]
            profit = res["net_profit"]
            
            total_costs += costs
            total_profit += profit
            
            item_product_cost = res["breakdown"].get(FinancialTransactionType.PRODUCT_COST.value, Decimal("0.00"))
            if item_product_cost > Decimal("0.00"):
                total_costed_revenue += item.sale_price_net  # Gerçek satış fiyatı
            
            funnel_gross += item.sale_price_net  # Gerçek satış fiyatı
            
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

        # Kâr Marjları
        profit_margin = Decimal("0.00")
        if toplam_ciro > Decimal("0.00"):
            profit_margin = (total_profit / toplam_ciro) * Decimal("100.00")
            
        profit_on_cost_ratio = Decimal("0.00")
        total_product_cost = breakdown.get(FinancialTransactionType.PRODUCT_COST.value, Decimal("0.00"))
        if total_product_cost > Decimal("0.00"):
            profit_on_cost_ratio = (total_profit / total_product_cost) * Decimal("100.00")

        # Kayıp Kaçak
        lost_and_leakage = (
            breakdown.get(FinancialTransactionType.PENALTY.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.RETURN_LOSS.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.EARLY_PAYMENT.value, Decimal("0"))
        )
        
        # --- Metrik Listeleri ---
        
        order_metrics = {
            "order_count": active_order_count,
            "total_order_count": total_orders,
            "cancelled_count": cancelled_count,
            "avg_revenue_per_order": str(round(toplam_ciro / active_order_count, 2)) if active_order_count > 0 else "0.00",
            "avg_profit_per_order": str(round(total_profit / active_order_count, 2)) if active_order_count > 0 else "0.00",
            "avg_cargo_per_order": str(round(total_cargo_cost / active_order_count, 2)) if active_order_count > 0 else "0.00",
        }
        
        product_metrics = {
            "items_sold": total_items_sold,
            "avg_revenue_per_item": str(round(toplam_ciro / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_profit_per_item": str(round(total_profit / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_cargo_per_item": str(round(total_cargo_cost / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_commission_rate": str(round((total_commission_cost / toplam_ciro)*100, 2)) if toplam_ciro > 0 else "0.00",
            "avg_discount_rate": str(round((total_discount / total_gross)*100, 2)) if total_gross > 0 else "0.00",
        }
        
        # İade Metrikleri
        return_loss_val = breakdown.get(FinancialTransactionType.RETURN_LOSS.value, Decimal("0.00"))
        returned_orders_count = orders_qs.filter(status__in=["Returned", "Cancelled"]).count()
        real_return_rate = Decimal("0.00")
        if total_orders > 0:
            real_return_rate = round(Decimal(returned_orders_count) / Decimal(total_orders) * Decimal("100"), 2)
        
        returned_items = OrderItem.objects.filter(order__in=orders_qs.filter(status__in=["Returned", "Cancelled"]))
        total_return_cargo_loss = Decimal("0.00")
        for r_item in returned_items:
            r_info = ProfitCalculator.calculate_for_order_item(r_item)
            total_return_cargo_loss += r_info["breakdown"].get(FinancialTransactionType.SHIPPING_FEE.value, Decimal("0.00"))
        
        return_metrics = {
            "return_rate": str(real_return_rate),
            "total_return_cost": str(return_loss_val + total_return_cargo_loss),
            "return_cargo_loss": str(total_return_cargo_loss),
            "overseas_operation_fee": "0.00"
        }
        
        # Reklam Metrikleri
        ads_val = breakdown.get(FinancialTransactionType.ADS_COST.value, Decimal("0.00"))
        ads_metrics = {
            "total_ads_cost": str(ads_val),
            "influencer_cut": "0.00",
            "ads_profit_index": str(round((ads_val / total_profit)*100, 2)) if total_profit > 0 else "0.00",
            "ads_revenue_index": str(round((ads_val / toplam_ciro)*100, 2)) if toplam_ciro > 0 else "0.00",
        }
        
        # Net Kâr Performansı Hunisi
        net_profit_funnel = [
            {"name": "Ciro", "value": str(funnel_gross)},
            {"name": "Kargo Düşülmüş", "value": str(funnel_gross - funnel_cargo)},
            {"name": "Pazaryeri Masrafı Düşülmüş", "value": str(funnel_gross - funnel_cargo - funnel_marketplace_fees)},
            {"name": "Vergi Düşülmüş", "value": str(funnel_gross - funnel_cargo - funnel_marketplace_fees - funnel_taxes)},
            {"name": "Kâr", "value": str(funnel_net)},
        ]
        
        # Kâr Performansı History (Area Chart)
        from datetime import timedelta
        from django.db.models.functions import TruncDate
        from django.db.models import Sum
        
        history = []
        day_range = 30
        start_day = timezone.now() - timedelta(days=day_range)
        daily_orders = active_orders_qs.filter(order_date__gte=start_day).annotate(day=TruncDate('order_date')).values('day').annotate(
            day_revenue=Sum('items__sale_price_net')
        ).order_by('day')
        
        daily_profit_map = {}
        total_daily_revenue = sum(d['day_revenue'] or 0 for d in daily_orders)
        for d in daily_orders:
            day_str = format_date_short_tr(d['day']) if d['day'] else "?"
            day_revenue = d['day_revenue'] or Decimal("0")
            if total_daily_revenue > 0:
                day_profit = total_profit * (day_revenue / Decimal(str(total_daily_revenue)))
            else:
                day_profit = Decimal("0")
            daily_profit_map[day_str] = round(day_profit, 2)
        
        for i in range(13, -1, -1):
            day = format_date_short_tr(timezone.now() - timedelta(days=i))
            history.append({
                "date": day,
                "profit": str(daily_profit_map.get(day, Decimal("0.00")))
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
        
        low_stock_list = sorted(low_stock_list, key=lambda x: x["current_stock"])[:5]

        return Response({
            "kpis": {
                "total_orders": active_order_count,
                "gross_revenue": str(total_gross),
                "toplam_ciro": str(toplam_ciro),          # Toplam Ciro = SUM(sale_price_net) from order items
                "costed_revenue": str(total_costed_revenue),  # Maliyetlendirilen Ciro
                "net_revenue": str(toplam_ciro),           # Keep backward compat
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
        import requests as http_requests
        import logging
        logger = logging.getLogger(__name__)

        api_key = request.data.get("api_key", "").strip()
        api_secret = request.data.get("api_secret", "").strip()
        supplier_id = request.data.get("supplier_id", "").strip()

        if not all([api_key, api_secret, supplier_id]):
            return Response({"ok": False, "message": "Eksik bilgi: api_key, api_secret veya supplier_id gerekli."}, status=400)

        # CRITICAL: Correct base URL per official Trendyol docs:
        # apigw.trendyol.com/integration/ (NOT api.trendyol.com/sapigw/ which is Cloudflare-blocked)
        url = f"https://apigw.trendyol.com/integration/product/sellers/{supplier_id}/products"
        params = {"approved": "true", "page": 0, "size": 1}
        headers = {
            "User-Agent": f"{supplier_id} - SelfIntegration",
            "Accept": "application/json",
        }

        # Debug logging (secrets redacted)
        logger.info(f"[TestConnection] URL: {url}")
        logger.info(f"[TestConnection] Params: {params}")
        logger.info(f"[TestConnection] User-Agent: {headers['User-Agent']}")
        logger.info(f"[TestConnection] Auth: ({api_key[:4]}...***)")
        
        # Detect server public IP for diagnostics
        server_ip = "bilinmiyor"
        try:
            ip_resp = http_requests.get("https://api.ipify.org", timeout=5)
            if ip_resp.ok:
                server_ip = ip_resp.text.strip()
        except Exception:
            pass
        
        try:
            res = http_requests.get(url, auth=(api_key, api_secret), params=params, headers=headers, timeout=30)
            
            # Debug: Log response info
            request_id = res.headers.get("x-request-id", "N/A")
            logger.info(f"[TestConnection] Status: {res.status_code}, x-request-id: {request_id}")
            logger.info(f"[TestConnection] Response body preview: {res.text[:200]}")
            
            if not res.ok:
                text = res.text
                status = res.status_code
                message = text[:300]
                
                # HTML check (Cloudflare block)
                if '<html' in text.lower() or 'cloudflare' in text.lower():
                    message = (
                        f"Cloudflare tarafından engellendiniz (HTTP {status}). "
                        f"Sunucu IP adresiniz: {server_ip} — "
                        "Bu IP'nin Trendyol Satıcı Paneli'nde API whitelist'ine eklendiğinden emin olun. "
                        "Ekleme sonrası yayılması 10-30 dakika sürebilir."
                    )
                elif status == 401:
                    message = "API Key veya API Secret hatalı. Lütfen kontrol edip tekrar deneyin."
                elif status == 403:
                    message = f"Erişim reddedildi (403). Sunucu IP: {server_ip}. Trendyol whitelist'ini kontrol edin."
                elif status == 429:
                    message = "Çok fazla istek gönderildi. Lütfen biraz bekleyip tekrar deneyin."
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
                    "request_id": request_id,
                    "server_ip": server_ip,
                }, status=400)
                
            data = res.json()
            return Response({
                "ok": True,
                "sample_product_count_hint": data.get("totalElements", 0),
                "request_id": request_id,
            })
            
        except http_requests.RequestException as e:
            logger.error(f"[TestConnection] Network error: {e}")
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
                "supplier_id": ""
            })

        return Response({
            "api_key": account.api_key,
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
        sync_result = None
        if auto_sync and account.api_key and account.api_secret:
            try:
                sync_all_trendyol_data_task(str(account.id))
                sync_result = "success"
            except ValueError as e:
                # Credentials saved but sync failed (e.g. Cloudflare block)
                # Don't fail — let user know credentials are saved
                sync_result = f"sync_failed: {str(e)}"
            except Exception as e:
                sync_result = f"sync_error: {str(e)}"

        return Response({
            "message": "Trendyol API bilgileri başarıyla kaydedildi.",
            "sync_started": auto_sync,
            "sync_result": sync_result,
        })


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
        from django.db.models import Q
        from rest_framework.pagination import PageNumberPagination
        from django.utils import timezone
        import datetime
        
        two_months_ago = timezone.now() - datetime.timedelta(days=60)
        
        from django.db.models import Max
        
        # Paginate by unique marketplace_skus (Model Codes)
        skus_qs = Product.objects.filter(
            organization=org,
            is_active=True
        ).values('marketplace_sku').annotate(
            latest_created_at=Max('trendyol_created_at')
        ).order_by('-latest_created_at')

        search = request.GET.get('search', '').strip()
        if search:
            skus_qs = skus_qs.filter(
                Q(title__icontains=search) |
                Q(barcode__icontains=search) |
                Q(marketplace_sku__icontains=search) |
                Q(variants__barcode__icontains=search) |
                Q(variants__title__icontains=search)
            ).distinct()
            
        paginator = PageNumberPagination()
        paginator.page_size = 50
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100
        
        paginated_skus = paginator.paginate_queryset(skus_qs, request)
        current_skus = [item['marketplace_sku'] for item in paginated_skus]
        
        # Fetch full data for these SKUs
        products = Product.objects.filter(
            organization=org,
            marketplace_sku__in=current_skus,
            is_active=True
        ).prefetch_related('variants').order_by(
            django_models.F('trendyol_created_at').desc(nulls_last=True)
        )
        
        # Simple serialization
        data = []
        for p in products:
            product_data = {
                "id": p.id,
                "title": p.title,
                "barcode": p.barcode,
                "marketplace_sku": p.marketplace_sku,
                "trendyol_content_id": p.trendyol_content_id,
                "currency": p.currency,
                "sale_price": str(p.sale_price),
                "vat_rate": str(p.vat_rate),
                "commission_rate": str(p.commission_rate),
                "image_url": p.image_url,
                "desi": str(p.desi),
                "default_carrier": p.default_carrier,
                "brand": p.brand,
                "return_rate": str(p.return_rate),
                "fast_delivery": p.fast_delivery,
                "current_stock": p.current_stock,
                "is_active": p.is_active,
                "variants": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "barcode": v.barcode,
                        "marketplace_sku": v.marketplace_sku,
                        "cost_price": str(v.cost_price),
                        "cost_vat_rate": str(v.cost_vat_rate),
                        "desi": str(v.desi) if v.desi is not None else None,
                        "color": v.color,
                        "size": v.size,
                        "stock": v.stock,
                        "extra_cost_rate": str(v.extra_cost_rate),
                        "extra_cost_amount": str(v.extra_cost_amount),
                    } for v in p.variants.all()
                ]
            }
            data.append(product_data)

        # Total count should be count of distinct SKUs
        return paginator.get_paginated_response(data)

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

            if "vat_rate" in request.data:
                try:
                    product.vat_rate = Decimal(str(request.data["vat_rate"]))
                except Exception:
                    return Response({"error": "Invalid vat_rate format"}, status=400)
                    
            if "fast_delivery" in request.data:
                product.fast_delivery = bool(request.data["fast_delivery"])
                
            product.save()
            
            return Response({
                "id": product.id,
                "desi": str(product.desi),
                "default_carrier": product.default_carrier,
                "return_rate": str(product.return_rate),
                "vat_rate": str(product.vat_rate),
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
            profile = request.user.profile
            org = profile.organization
        except Exception:
            return Response({"error": "Organizasyon bulunamadı"}, status=400)

        from core.models import Order
        from core.services.profit_calculator import ProfitCalculator
        from decimal import Decimal
        
        # Sadece bu organizasyona ait olan siparişleri getir, iptal edilenleri hariç tut
        # prefetch_related ile db call optimizasyonu
        CANCELLED_STATUSES = ['Cancelled', 'Canceled', 'İptal', 'iptal', 'CANCELLED', 'CANCELED']
        orders = Order.objects.filter(marketplace_account__organization=org).exclude(
            status__in=CANCELLED_STATUSES
        ).prefetch_related('items__product_variant__product', 'items__transactions').order_by('-order_date')
        
        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")

        if min_date_str and max_date_str:
            from datetime import datetime
            try:
                min_date = timezone.make_aware(datetime.strptime(min_date_str, "%Y-%m-%d"))
                max_date = timezone.make_aware(datetime.strptime(max_date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
                orders = orders.filter(order_date__gte=min_date, order_date__lte=max_date)
            except ValueError:
                pass
        else:
            # Sadece son 50 siparişi gönderelim (filtre yoksa)
            orders = orders[:50]

        data = []
        for order in orders:
            # Sipariş bazlı kârlılık hesabı — kargo ve hizmet bedeli TEK kez uygulanır
            calc = ProfitCalculator.calculate_for_order(order)
            kd   = calc["kdv_detail"]

            # Per-item display data (komisyon oranı ve fiyat için)
            items_data = []
            for item in order.items.all():
                item_r = ProfitCalculator.calculate_for_order_item(item)
                bd_item = item_r["breakdown"]
                title          = "Bilinmeyen Ürün"
                barcode        = item.sku
                commission_rate = item.applied_commission_rate or Decimal("0.00")
                image_url      = ""
                if item.product_variant and item.product_variant.product:
                    title      = item.product_variant.product.title
                    barcode    = item.product_variant.barcode
                    image_url  = item.product_variant.product.image_url or ""
                    if commission_rate == Decimal("0.00"):
                        commission_rate = item.product_variant.product.commission_rate
                items_data.append({
                    "id":               item.id,
                    "title":            title,
                    "barcode":          barcode,
                    "quantity":         item.quantity,
                    "sale_price_gross": str(item.sale_price_gross),
                    "commission_rate":  str(commission_rate),
                    "commission_cost":  str(bd_item.get("COMMISSION", Decimal("0.00"))),
                    "image_url":        image_url,
                })

            data.append({
                "id":             order.id,
                "order_number":   order.order_number,
                "order_date":     format_date_tr(order.order_date),
                "status":         order.status,
                "is_micro_export": order.channel == 'micro_export',
                "total_gross":    str(calc["total_sale"]),
                "total_profit":   str(calc["net_profit"]),
                "profit_margin":  str(calc["profit_margin"]),
                "profit_on_cost": str(calc["profit_on_cost"]),
                "items":          items_data,
                "aggregated_breakdown": {
                    "product_cost":       str(calc["product_cost"]),
                    "extra_cost":         str(calc["extra_product_cost"]),
                    "commission":         str(calc["commission"]),
                    "shipping_fee":       str(calc["cargo"]),
                    "cargo_source":       calc.get("cargo_source", "estimated"),
                    "service_fee":        str(calc["service_fee"]),
                    "withholding":        str(calc["withholding"]),
                    "net_kdv":            str(kd["net_kdv"]),
                    "satis_kdv":          str(kd["satis_kdv"]),
                    "alis_kdv":           str(kd["alis_kdv"]),
                    "kargo_kdv":          str(kd["kargo_kdv"]),
                    "komisyon_kdv":       str(kd["komisyon_kdv"]),
                    "hizmet_bedeli_kdv":  str(kd["hizmet_bedeli_kdv"]),
                },
            })

        return Response({"ok": True, "data": data})


class OrderExcelExportView(APIView):
    """
    GET /api/orders/export-excel/
    Sipariş kârlılık verilerini Excel olarak dışa aktarır.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            org = profile.organization
        except Exception:
            return Response({"error": "Organizasyon bulunamadı"}, status=400)

        from core.models import Order
        from core.services.profit_calculator import ProfitCalculator
        from decimal import Decimal
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment
        from io import BytesIO
        from django.http import HttpResponse

        orders = Order.objects.filter(
            marketplace_account__organization=org
        ).prefetch_related(
            'items__product_variant__product',
            'items__transactions'
        ).order_by('-order_date')

        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")

        if min_date_str and max_date_str:
            from datetime import datetime
            try:
                min_date = timezone.make_aware(datetime.strptime(min_date_str, "%Y-%m-%d"))
                max_date = timezone.make_aware(datetime.strptime(max_date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
                orders = orders.filter(order_date__gte=min_date, order_date__lte=max_date)
            except ValueError:
                pass
        else:
            orders = orders[:200]

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sipariş Kârlılık"

        header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=10)
        profit_fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
        loss_fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")

        columns = [
            "Sipariş Numarası", "Sipariş Tarihi", "Durum",
            "Sipariş Tutarı (₺)", "Ürün Maliyeti (₺)", "Ek Ürün Maliyeti (₺)",
            "Kargo Ücreti (₺)", "Komisyon Tutarı (₺)", "Hizmet Bedeli (₺)",
            "Stopaj Kesintisi (₺)", "Net KDV (₺)", "Kâr Tutarı (₺)",
            "Kâr Oranı (%)", "Kâr Marjı (%)",
        ]

        ws.append(columns)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 25
        for i, _ in enumerate(columns, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = 22

        for order in orders:
            total_gross = Decimal("0.00")
            total_profit = Decimal("0.00")
            bd = {k: Decimal("0.00") for k in ["product_cost", "extra_cost", "commission", "shipping_fee", "service_fee", "withholding", "net_kdv"]}

            for item in order.items.all():
                pi = ProfitCalculator.calculate_for_order_item(item)
                total_gross += pi["gross_revenue"]
                total_profit += pi["net_profit"]
                b = pi["breakdown"]
                bd["product_cost"] += b.get("PRODUCT_COST", Decimal("0.00"))
                bd["extra_cost"] += pi.get("extra_product_cost", Decimal("0.00"))
                bd["commission"] += b.get("COMMISSION", Decimal("0.00"))
                bd["shipping_fee"] += b.get("SHIPPING_FEE", Decimal("0.00"))
                bd["service_fee"] += b.get("SERVICE_FEE", Decimal("0.00"))
                bd["withholding"] += b.get("WITHHOLDING", Decimal("0.00"))
                bd["net_kdv"] += pi.get("kdv_detail", {}).get("net_kdv", Decimal("0.00"))

            profit_margin = round((total_profit / total_gross) * 100, 2) if total_gross > 0 else Decimal("0.00")
            profit_on_cost = round((total_profit / bd["product_cost"]) * 100, 2) if bd["product_cost"] > 0 else Decimal("0.00")
            base_cost = bd["product_cost"] - bd["extra_cost"]

            ws.append([
                order.order_number,
                format_date_tr(order.order_date),
                order.status,
                float(total_gross),
                float(base_cost),
                float(bd["extra_cost"]),
                float(bd["shipping_fee"]),
                float(bd["commission"]),
                float(bd["service_fee"]),
                float(bd["withholding"]),
                float(bd["net_kdv"]),
                float(total_profit),
                float(profit_on_cost),
                float(profit_margin),
            ])

            last_row = ws.max_row
            profit_cell = ws.cell(last_row, 12)
            if total_profit > 0:
                profit_cell.fill = profit_fill
            elif total_profit < 0:
                profit_cell.fill = loss_fill

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="Siparis_Karliligi.xlsx"'
        return response





class CategoryAnalysisView(APIView):
    """
    GET /api/reports/categories/
    Kategori bazlı kârlılık verilerini döndürür. min_date/max_date filtreleri destekler.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            org = profile.organization
        except Exception as e:
            return Response({"error": f"Organizasyon bulunamadı: {str(e)}"}, status=400)

        from core.models import OrderItem, Order, Product
        from core.services.profit_calculator import ProfitCalculator
        from decimal import Decimal
        from datetime import datetime, time

        orders = Order.objects.filter(marketplace_account__organization=org)
        
        # Tarih filtresi
        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")
        if min_date_str and max_date_str:
            try:
                min_date = timezone.make_aware(datetime.strptime(min_date_str, "%Y-%m-%d"))
                max_date = timezone.make_aware(datetime.combine(datetime.strptime(max_date_str, "%Y-%m-%d"), time.max))
                orders = orders.filter(order_date__gte=min_date, order_date__lte=max_date)
            except ValueError:
                pass

        items = OrderItem.objects.filter(
            order__in=orders,
            product_variant__isnull=False
        ).select_related('product_variant', 'product_variant__product', 'order').prefetch_related('transactions')

        category_map = {}

        for item in items:
            variant = item.product_variant
            if not variant or not variant.product:
                continue

            category = variant.product.category_name or "Kategorisiz"

            if category not in category_map:
                category_map[category] = {
                    "category": category,
                    "product_count": set(),
                    "total_sold_quantity": 0,
                    "total_sales_amount": Decimal("0.00"),
                    "total_profit": Decimal("0.00"),
                    "total_cost": Decimal("0.00"),
                    "total_commission": Decimal("0.00"),
                    "total_cargo": Decimal("0.00"),
                }

            profit_info = ProfitCalculator.calculate_for_order_item(item)
            bd = profit_info.get("breakdown", {})

            category_map[category]["product_count"].add(variant.product.id)
            category_map[category]["total_sold_quantity"] += item.quantity
            category_map[category]["total_sales_amount"] += profit_info["gross_revenue"]
            category_map[category]["total_profit"] += profit_info["net_profit"]
            category_map[category]["total_cost"] += bd.get("PRODUCT_COST", Decimal("0.00"))
            category_map[category]["total_commission"] += bd.get("COMMISSION", Decimal("0.00"))
            category_map[category]["total_cargo"] += bd.get("SHIPPING_FEE", Decimal("0.00"))

        data = []
        for cat, stats in category_map.items():
            total_sales = stats["total_sales_amount"]
            total_profit = stats["total_profit"]

            profit_margin = Decimal("0.00")
            if total_sales > Decimal("0.00"):
                profit_margin = round((total_profit / total_sales) * Decimal("100.00"), 2)

            data.append({
                "id": cat,
                "category": stats["category"],
                "product_count": len(stats["product_count"]),
                "total_sold_quantity": stats["total_sold_quantity"],
                "total_sales_amount": str(stats["total_sales_amount"]),
                "total_profit": str(stats["total_profit"]),
                "total_commission": str(stats["total_commission"]),
                "total_cargo": str(stats["total_cargo"]),
                "profit_margin": str(profit_margin),
            })

        data.sort(key=lambda x: Decimal(x["total_sales_amount"]), reverse=True)
        return Response({"ok": True, "data": data})


class ReturnAnalysisView(APIView):
    """
    GET /api/reports/returns/
    İade/iptal sipariş analizi döndürür. min_date/max_date filtreleri destekler.
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
        from datetime import datetime, time

        all_orders = Order.objects.filter(marketplace_account__organization=org)
        
        # Tarih filtresi
        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")
        if min_date_str and max_date_str:
            try:
                min_date = timezone.make_aware(datetime.strptime(min_date_str, "%Y-%m-%d"))
                max_date = timezone.make_aware(datetime.combine(datetime.strptime(max_date_str, "%Y-%m-%d"), time.max))
                all_orders = all_orders.filter(order_date__gte=min_date, order_date__lte=max_date)
            except ValueError:
                pass
        
        returned_orders = all_orders.filter(status__in=["Returned", "Cancelled"])

        total_order_count = all_orders.count()
        returned_order_count = returned_orders.count()

        return_rate = Decimal("0.00")
        if total_order_count > 0:
            return_rate = round(Decimal(returned_order_count) / Decimal(total_order_count) * Decimal("100"), 2)

        # Toplam satış tutarını hesapla (tüm siparişlerden)
        all_items = OrderItem.objects.filter(order__in=all_orders)
        total_sales_amount = sum(item.sale_price_gross for item in all_items)

        items = OrderItem.objects.filter(
            order__in=returned_orders,
            product_variant__isnull=False
        ).select_related('product_variant', 'product_variant__product', 'order').prefetch_related('transactions')

        product_return_map = {}
        total_return_cargo_loss = Decimal("0.00")
        total_return_revenue_loss = Decimal("0.00")

        for item in items:
            variant = item.product_variant
            if not variant or not variant.product:
                continue

            barcode = variant.barcode or ""
            if not barcode:
                continue

            profit_info = ProfitCalculator.calculate_for_order_item(item)
            bd = profit_info.get("breakdown", {})
            shipping_cost = bd.get("SHIPPING_FEE", Decimal("0.00"))

            total_return_cargo_loss += shipping_cost
            total_return_revenue_loss += profit_info["gross_revenue"]

            if barcode not in product_return_map:
                product_return_map[barcode] = {
                    "barcode": barcode,
                    "title": variant.product.title,
                    "category": variant.product.category_name or "",
                    "return_count": 0,
                    "cargo_loss": Decimal("0.00"),
                    "revenue_loss": Decimal("0.00"),
                }

            product_return_map[barcode]["return_count"] += item.quantity
            product_return_map[barcode]["cargo_loss"] += shipping_cost
            product_return_map[barcode]["revenue_loss"] += profit_info["gross_revenue"]

        product_returns = []
        for stats in product_return_map.values():
            product_returns.append({
                "barcode": stats["barcode"],
                "title": stats["title"],
                "category": stats["category"],
                "return_count": stats["return_count"],
                "cargo_loss": str(stats["cargo_loss"]),
                "revenue_loss": str(stats["revenue_loss"]),
            })

        product_returns.sort(key=lambda x: int(x["return_count"]), reverse=True)
        
        # İade/Satış oranı
        return_to_sales_ratio = Decimal("0.00")
        if total_sales_amount > Decimal("0.00"):
            return_to_sales_ratio = round(total_return_revenue_loss / total_sales_amount * Decimal("100"), 2)

        return Response({
            "ok": True,
            "summary": {
                "total_orders": total_order_count,
                "returned_orders": returned_order_count,
                "return_rate": str(return_rate),
                "total_return_cargo_loss": str(total_return_cargo_loss),
                "total_return_revenue_loss": str(total_return_revenue_loss),
                "return_to_sales_ratio": str(return_to_sales_ratio),
            },
            "data": product_returns
        })


class AdsAnalysisView(APIView):
    """
    GET /api/reports/ads/
    Reklam analizi: filtrelenen tarih aralığında reklam harcamalarını, satış ve kâr verilerini döndürür.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            org = profile.organization
        except Exception as e:
            return Response({"error": f"Organizasyon bulunamadı: {str(e)}"}, status=400)

        from core.models import OrderItem, Order, FinancialTransaction
        from core.services.profit_calculator import ProfitCalculator
        from decimal import Decimal
        from datetime import datetime, time

        # Tarih filtresi
        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")
        
        orders = Order.objects.filter(marketplace_account__organization=org)
        ads_txns = FinancialTransaction.objects.filter(
            organization=org,
            transaction_type=FinancialTransactionType.ADS_COST.value,
        )
        
        if min_date_str and max_date_str:
            try:
                min_date = timezone.make_aware(datetime.strptime(min_date_str, "%Y-%m-%d"))
                max_date = timezone.make_aware(datetime.combine(datetime.strptime(max_date_str, "%Y-%m-%d"), time.max))
                orders = orders.filter(order_date__gte=min_date, order_date__lte=max_date)
                ads_txns = ads_txns.filter(occurred_at__gte=min_date, occurred_at__lte=max_date)
            except ValueError:
                pass

        # Reklam harcaması toplamı
        total_ads_cost = sum(abs(txn.amount) for txn in ads_txns)
        
        # Influencer kesintisi (şimdilik "OTHER" type ile tutulabilir, ya da 0)
        influencer_cost = Decimal("0.00")

        # Siparişlerden toplam satış ve kâr
        items = OrderItem.objects.filter(order__in=orders).select_related(
            'product_variant', 'product_variant__product', 'order'
        ).prefetch_related('transactions')
        
        total_sales = Decimal("0.00")
        total_profit = Decimal("0.00")
        
        for item in items:
            profit_info = ProfitCalculator.calculate_for_order_item(item)
            total_sales += profit_info["gross_revenue"]
            total_profit += profit_info["net_profit"]

        # Oranlar
        ads_to_sales_ratio = Decimal("0.00")
        ads_to_profit_ratio = Decimal("0.00")
        if total_sales > Decimal("0.00"):
            ads_to_sales_ratio = round(total_ads_cost / total_sales * Decimal("100"), 2)
        if total_profit > Decimal("0.00"):
            ads_to_profit_ratio = round(total_ads_cost / total_profit * Decimal("100"), 2)

        return Response({
            "ok": True,
            "data": {
                "total_ads_cost": str(total_ads_cost),
                "influencer_cost": str(influencer_cost),
                "total_sales": str(total_sales),
                "total_profit": str(total_profit),
                "ads_to_sales_ratio": str(ads_to_sales_ratio),
                "ads_to_profit_ratio": str(ads_to_profit_ratio),
            }
        })


import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.http import HttpResponse

class ProductExcelExportView(APIView):
    """
    GET /api/products/export-excel/
    13 sütunlu Excel dosyası oluşturur.
    Sütunlar: Barkod, Model Kodu, Stok Kodu, Kategori İsmi, Ürün Adı,
              Trendyol Satış Fiyatı, Stok, Ürün Maliyeti (KDV Dahil),
              Maliyet KDV Oranı, Para Birimi, Ürün Desisi,
              Ekstra Maliyet (%), Ekstra Maliyet (TL)
    Mavi = Trendyol'dan otomatik doldurulur (salt okunur)
    Sarı  = Kullanıcı tarafından düzenlenir
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.models import UserProfile, Product
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        org = profile.organization

        products = Product.objects.filter(organization=org, is_active=True).prefetch_related('variants').order_by(
            django_models.F('trendyol_created_at').desc(nulls_last=True)
        )

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Urun Maliyetleri"

        # Column definitions: (header, editable)
        COLUMNS = [
            ("Barkod",                    False),  # 1  — Trendyol
            ("Model Kodu",                False),  # 2  — Trendyol
            ("Stok Kodu",                 False),  # 3  — Trendyol
            ("Kategori İsmi",             False),  # 4  — Trendyol
            ("Ürün Adı",                  False),  # 5  — Trendyol
            ("Trendyol Satış Fiyatı",     False),  # 6  — Trendyol
            ("Stok",                      False),  # 7  — Trendyol
            ("Ürün Maliyeti (KDV Dahil)", True),   # 8  — Kullanıcı
            ("Maliyet KDV Oranı",         True),   # 9  — Kullanıcı (default: Trendyol KDV)
            ("Para Birimi",               False),  # 10 — Trendyol
            ("Ürün Desisi",               True),   # 11 — Kullanıcı (default: 1)
            ("Ekstra Maliyet (%)",        True),   # 12 — Kullanıcı
            ("Ekstra Maliyet (TL)",       True),   # 13 — Kullanıcı
        ]

        info_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")  # mavi
        edit_fill = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")  # sarı
        header_font = Font(bold=True)

        for col_num, (header_title, editable) in enumerate(COLUMNS, 1):
            cell = ws.cell(row=1, column=col_num, value=header_title)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            cell.fill = edit_fill if editable else info_fill

        row_num = 2
        for product in products:
            for variant in product.variants.all():
                desi_val = float(variant.desi) if variant.desi is not None else float(product.desi if product.desi else 1)
                # Maliyet KDV Oranı: Kullanıcı girdiyse onu göster, yoksa Trendyol satış KDV'sini default al
                cost_vat = float(variant.cost_vat_rate) if variant.cost_vat_rate else float(product.vat_rate)

                ws.cell(row=row_num, column=1,  value=variant.barcode)
                ws.cell(row=row_num, column=2,  value=product.marketplace_sku)
                ws.cell(row=row_num, column=3,  value=variant.marketplace_sku or "")
                ws.cell(row=row_num, column=4,  value=product.category_name or "")
                ws.cell(row=row_num, column=5,  value=variant.title or product.title)
                ws.cell(row=row_num, column=6,  value=float(product.sale_price))
                ws.cell(row=row_num, column=7,  value=variant.stock)
                ws.cell(row=row_num, column=8,  value=float(variant.cost_price))
                ws.cell(row=row_num, column=9,  value=cost_vat)
                ws.cell(row=row_num, column=10, value=product.currency or "TRY")
                ws.cell(row=row_num, column=11, value=desi_val)
                ws.cell(row=row_num, column=12, value=float(variant.extra_cost_rate))
                ws.cell(row=row_num, column=13, value=float(variant.extra_cost_amount))
                row_num += 1

        # Auto column widths
        for col in ws.columns:
            max_length = max((len(str(cell.value or "")) for cell in col), default=0)
            ws.column_dimensions[col[0].column_letter].width = min(max_length + 4, 50)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = "attachment; filename*=UTF-8''Urun_Maliyetleri.xlsx"
        wb.save(response)
        return response


class ProductExcelImportView(APIView):
    """
    POST /api/products/import-excel/
    Excel dosyasındaki maliyet, KDV, desi ve ekstra maliyet bilgilerini veritabanına kaydeder.
    Zorunlu: Barkod
    Desteklenen sütunlar: Ürün Maliyeti (KDV Dahil), Maliyet KDV Oranı, Ürün Desisi,
                          Ekstra Maliyet (%), Ekstra Maliyet (TL)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from core.models import UserProfile, ProductVariant
        from decimal import Decimal

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        org = profile.organization

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Dosya bulunamadı."}, status=400)
        if not (file.name.endswith('.xlsx') or file.name.endswith('.xls')):
            return Response({"error": "Geçersiz dosya formatı. Lütfen .xlsx veya .xls yükleyin."}, status=400)

        def parse_decimal(val):
            if val is None or str(val).strip() == "":
                return None
            try:
                s = str(val).strip()
                if ',' in s and '.' in s:
                    s = s.replace('.', '').replace(',', '.')
                elif ',' in s:
                    s = s.replace(',', '.')
                return Decimal(s)
            except Exception:
                return None

        def parse_barcode(raw):
            if raw is None:
                return None
            if isinstance(raw, float):
                return str(int(raw)).strip()
            s = str(raw).strip()
            return s[:-2] if s.endswith('.0') else s

        try:
            wb = openpyxl.load_workbook(file, data_only=True)
            ws = wb.active

            headers = {}
            for idx, cell in enumerate(ws[1]):
                if cell.value:
                    headers[str(cell.value).strip()] = idx

            def get_col(names):
                for n in names:
                    if n in headers:
                        return headers[n]
                return None

            idx_barkod       = get_col(["Barkod"])
            idx_cost         = get_col(["Ürün Maliyeti (KDV Dahil)", "KDV Dahil Maliyet", "Ürün Maliyeti ( KDV Dahil)"])
            idx_vat          = get_col(["Maliyet KDV Oranı", "KDV Oranı"])
            idx_desi         = get_col(["Ürün Desisi", "Desi"])
            idx_extra_rate   = get_col(["Ekstra Maliyet (%)"])
            idx_extra_amount = get_col(["Ekstra Maliyet (TL)"])

            if idx_barkod is None:
                return Response({"error": "Eksik sütun: 'Barkod' sütunu bulunamadı."}, status=400)
            if idx_cost is None:
                return Response({"error": "Eksik sütun: 'Ürün Maliyeti (KDV Dahil)' sütunu bulunamadı."}, status=400)

            updated_variants = 0
            unmatched_barcodes = []

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row:
                    continue
                barcode = parse_barcode(row[idx_barkod])
                if not barcode:
                    continue

                variant = ProductVariant.objects.select_related('product').filter(
                    barcode=barcode, product__organization=org
                ).first()
                if variant is None:
                    unmatched_barcodes.append(barcode)
                    continue

                try:
                    variant_fields = []
                    product_fields = []

                    clean_cost = parse_decimal(row[idx_cost])
                    if clean_cost is not None:
                        variant.cost_price = clean_cost
                        variant_fields.append("cost_price")

                    if idx_vat is not None:
                        clean_vat = parse_decimal(row[idx_vat])
                        if clean_vat is not None:
                            variant.cost_vat_rate = clean_vat
                            variant_fields.append("cost_vat_rate")

                    if idx_desi is not None:
                        clean_desi = parse_decimal(row[idx_desi])
                        if clean_desi is not None:
                            variant.desi = clean_desi
                            variant_fields.append("desi")
                            variant.product.desi = clean_desi
                            product_fields.append("desi")

                    if idx_extra_rate is not None:
                        clean_rate = parse_decimal(row[idx_extra_rate])
                        if clean_rate is not None:
                            variant.extra_cost_rate = clean_rate
                            variant_fields.append("extra_cost_rate")

                    if idx_extra_amount is not None:
                        clean_amount = parse_decimal(row[idx_extra_amount])
                        if clean_amount is not None:
                            variant.extra_cost_amount = clean_amount
                            variant_fields.append("extra_cost_amount")

                    if product_fields:
                        variant.product.save(update_fields=list(set(product_fields)))
                    if variant_fields:
                        variant.save(update_fields=variant_fields)
                    updated_variants += 1

                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Excel import row error (barcode={barcode}): {e}")

            msg = f"{updated_variants} varyant başarıyla güncellendi."
            if unmatched_barcodes:
                msg += f" {len(unmatched_barcodes)} barkod sistemde bulunamadı."

            return Response({"ok": True, "message": msg, "updated_count": updated_variants, "unmatched_count": len(unmatched_barcodes)})

        except Exception as e:
            return Response({"error": f"Excel dosyası okunamadı: {str(e)}"}, status=500)


class LivePerformanceView(APIView):
    """
    GET /api/live-performance/
    Canlı Performans sayfası için tek endpoint.
    Bugünün (veya filtre aralığının) sipariş kârlılığını, saatlik performansı,
    ürün heatmap'ini ve akıllı önerileri döndürür.
    Tüm finansal hesaplamalar backend'de Decimal ile yapılır.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.models import UserProfile, Organization, ReturnClaim
        from core.services.profit_calculator import ProfitCalculator
        from datetime import datetime as dt_cls, time as dt_time, timedelta
        from django.db.models.functions import TruncHour
        from django.db.models import Sum as DjSum, Count
        from collections import defaultdict
        from rest_framework.pagination import PageNumberPagination

        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization
        if not org:
            org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
            profile.organization = org
            profile.save()

        # ── Date range (default: today) ──
        min_date_str = request.query_params.get("min_date")
        max_date_str = request.query_params.get("max_date")

        import zoneinfo
        tz_istanbul = zoneinfo.ZoneInfo("Europe/Istanbul")

        if min_date_str and max_date_str:
            try:
                min_date = dt_cls.strptime(min_date_str, "%Y-%m-%d").replace(tzinfo=tz_istanbul)
                max_date = dt_cls.combine(
                    dt_cls.strptime(max_date_str, "%Y-%m-%d").date(), dt_time.max
                ).replace(tzinfo=tz_istanbul)
            except ValueError:
                min_date = dt_cls.combine(timezone.localtime(timezone.now(), tz_istanbul).date(), dt_time.min).replace(tzinfo=tz_istanbul)
                max_date = dt_cls.combine(timezone.localtime(timezone.now(), tz_istanbul).date(), dt_time.max).replace(tzinfo=tz_istanbul)
        else:
            today = timezone.localtime(timezone.now(), tz_istanbul).date()
            min_date = dt_cls.combine(today, dt_time.min).replace(tzinfo=tz_istanbul)
            max_date = dt_cls.combine(today, dt_time.max).replace(tzinfo=tz_istanbul)

        # ── Base queryset ──
        orders_qs = Order.objects.filter(
            organization=org,
            order_date__gte=min_date,
            order_date__lte=max_date,
        ).exclude(
            status__in=["Cancelled", "Returned", "UnSupplied"]
        ).prefetch_related(
            'items__product_variant__product',
            'items__transactions'
        ).select_related('marketplace_account').order_by('-order_date')

        # ── Advanced Filters ──
        product_filter = request.query_params.get("product", "").strip()
        category_filter = request.query_params.get("category", "").strip()

        if product_filter:
            orders_qs = orders_qs.filter(
                items__product_variant__product__title__icontains=product_filter
            ).distinct()

        if category_filter:
            orders_qs = orders_qs.filter(
                items__product_variant__product__category_name__icontains=category_filter
            ).distinct()

        # ── Compute per-order profits ──
        all_order_rows = []
        product_agg = defaultdict(lambda: {
            "total_sales": 0, "total_revenue": Decimal("0"), "total_profit": Decimal("0"),
            "product_name": "", "return_rate": Decimal("0"), "category": ""
        })

        # Hourly aggregation buckets
        hourly_data = defaultdict(lambda: {"revenue": Decimal("0"), "profit": Decimal("0"), "order_count": 0})

        total_revenue = Decimal("0")
        total_profit = Decimal("0")
        total_commission = Decimal("0")
        total_cargo = Decimal("0")
        total_service_fee = Decimal("0")
        order_count = 0

        for order in orders_qs:
            calc = ProfitCalculator.calculate_for_order(order)
            order_profit = calc["net_profit"]
            order_sale = calc["total_sale"]
            order_commission = calc["commission"]
            order_cargo = calc["cargo"]
            order_service = calc["service_fee"]
            profit_margin = calc["profit_margin"]

            total_revenue += order_sale
            total_profit += order_profit
            total_commission += order_commission
            total_cargo += order_cargo
            total_service_fee += order_service
            order_count += 1

            # Determine main product name from first item
            product_name = "Bilinmeyen Ürün"
            product_cost = calc["product_cost"]
            return_rate = Decimal("0")
            category_name = ""

            first_item = order.items.all()[:1]
            if first_item:
                fi = first_item[0]
                if fi.product_variant and fi.product_variant.product:
                    product_name = fi.product_variant.product.title
                    return_rate = fi.product_variant.product.return_rate or Decimal("0")
                    category_name = fi.product_variant.product.category_name or ""

            # Return risk based on product return_rate
            if return_rate >= Decimal("20"):
                return_risk = "high"
            elif return_rate >= Decimal("10"):
                return_risk = "medium"
            else:
                return_risk = "low"

            kd = calc.get("kdv_detail", {})
            net_kdv = kd.get("net_kdv", Decimal("0"))

            order_row = {
                "order_number": order.order_number,
                "order_date": order.order_date.isoformat(),
                "product_name": product_name,
                "sale_price": str(order_sale),
                "cost": str(product_cost),
                "commission": str(order_commission),
                "cargo_cost": str(order_cargo),
                "tax": str(net_kdv),
                "net_profit": str(order_profit),
                "profit_margin": str(profit_margin),
                "return_risk": return_risk,
                "status": order.status,
                "cost_breakdown": {
                    "commission": str(order_commission),
                    "cargo": str(order_cargo),
                    "tax": str(net_kdv),
                    "service_fee": str(order_service),
                    "withholding": str(calc["withholding"]),
                    "product_cost": str(product_cost),
                }
            }
            all_order_rows.append(order_row)

            # Aggregate for product heatmap
            pk = product_name
            product_agg[pk]["product_name"] = product_name
            product_agg[pk]["total_sales"] += 1
            product_agg[pk]["total_revenue"] += order_sale
            product_agg[pk]["total_profit"] += order_profit
            product_agg[pk]["return_rate"] = return_rate
            product_agg[pk]["category"] = category_name

            # Hourly aggregation
            order_hour = timezone.localtime(order.order_date, tz_istanbul)
            hour_key = order_hour.strftime("%H:00")
            hourly_data[hour_key]["revenue"] += order_sale
            hourly_data[hour_key]["profit"] += order_profit
            hourly_data[hour_key]["order_count"] += 1

        # ── Post-filter: profit range & loss-only ──
        min_profit = request.query_params.get("min_profit")
        max_profit = request.query_params.get("max_profit")
        loss_only = request.query_params.get("loss_only", "").lower() == "true"

        filtered_rows = all_order_rows
        if loss_only:
            filtered_rows = [r for r in filtered_rows if Decimal(r["net_profit"]) < Decimal("0")]
        if min_profit:
            try:
                mp = Decimal(min_profit)
                filtered_rows = [r for r in filtered_rows if Decimal(r["net_profit"]) >= mp]
            except Exception:
                pass
        if max_profit:
            try:
                mp = Decimal(max_profit)
                filtered_rows = [r for r in filtered_rows if Decimal(r["net_profit"]) <= mp]
            except Exception:
                pass

        # ── Sort support ──
        sort_by = request.query_params.get("sort_by", "order_date")
        sort_dir = request.query_params.get("sort_dir", "desc")
        reverse = sort_dir == "desc"

        sortable_decimal_fields = ["sale_price", "cost", "commission", "cargo_cost", "tax", "net_profit", "profit_margin"]
        if sort_by in sortable_decimal_fields:
            filtered_rows.sort(key=lambda r: Decimal(r.get(sort_by, "0")), reverse=reverse)
        elif sort_by == "order_date":
            filtered_rows.sort(key=lambda r: r.get("order_date", ""), reverse=reverse)
        elif sort_by == "product_name":
            filtered_rows.sort(key=lambda r: r.get("product_name", "").lower(), reverse=reverse)

        # ── Paginate orders ──
        total_count = len(filtered_rows)
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_rows = filtered_rows[start_idx:end_idx]

        # ── KPIs ──
        profit_margin_pct = Decimal("0")
        if total_revenue > Decimal("0"):
            profit_margin_pct = (total_profit / total_revenue * Decimal("100")).quantize(Decimal("0.01"))

        net_cash_inflow = total_revenue - total_commission - total_cargo - total_service_fee
        avg_order_profit = (total_profit / Decimal(str(order_count))).quantize(Decimal("0.01")) if order_count > 0 else Decimal("0")

        kpis = {
            "total_revenue": str(total_revenue.quantize(Decimal("0.01"))),
            "net_profit": str(total_profit.quantize(Decimal("0.01"))),
            "profit_margin": str(profit_margin_pct),
            "net_cash_inflow": str(net_cash_inflow.quantize(Decimal("0.01"))),
            "order_count": order_count,
            "avg_order_profit": str(avg_order_profit),
        }

        # ── Hourly performance (fill missing hours) ──
        hourly_list = []
        for h in range(24):
            hk = f"{h:02d}:00"
            entry = hourly_data.get(hk, {"revenue": Decimal("0"), "profit": Decimal("0"), "order_count": 0})
            hourly_list.append({
                "hour": hk,
                "revenue": str(entry["revenue"].quantize(Decimal("0.01"))),
                "profit": str(entry["profit"].quantize(Decimal("0.01"))),
                "order_count": entry["order_count"],
            })

        # ── Product heatmap (sorted by profit desc) ──
        heatmap = []
        for pk, agg in product_agg.items():
            margin = Decimal("0")
            if agg["total_revenue"] > Decimal("0"):
                margin = (agg["total_profit"] / agg["total_revenue"] * Decimal("100")).quantize(Decimal("0.01"))
            heatmap.append({
                "product_name": agg["product_name"],
                "category": agg["category"],
                "total_sales": agg["total_sales"],
                "total_revenue": str(agg["total_revenue"].quantize(Decimal("0.01"))),
                "total_profit": str(agg["total_profit"].quantize(Decimal("0.01"))),
                "margin": str(margin),
                "return_rate": str(agg["return_rate"]),
            })
        heatmap.sort(key=lambda x: Decimal(x["total_profit"]), reverse=True)

        # ── Smart Insights (rule-based) ──
        insights = []
        for pk, agg in product_agg.items():
            margin = Decimal("0")
            if agg["total_revenue"] > Decimal("0"):
                margin = (agg["total_profit"] / agg["total_revenue"] * Decimal("100")).quantize(Decimal("0.01"))

            # Negative profit warning
            if agg["total_profit"] < Decimal("0"):
                insights.append({
                    "type": "danger",
                    "title": "Zarar Eden Ürün",
                    "message": f"\"{agg['product_name']}\" bugün ₺{abs(agg['total_profit']).quantize(Decimal('0.01'))} zarar etti. Fiyatlandırma ve maliyetleri gözden geçirin.",
                    "product_name": agg["product_name"],
                })
            # High sales but low margin
            elif agg["total_sales"] >= 3 and margin < Decimal("10") and margin >= Decimal("0"):
                insights.append({
                    "type": "suggestion",
                    "title": "Fiyat Artışı Önerisi",
                    "message": f"\"{agg['product_name']}\" {agg['total_sales']} satış yaptı ama kâr marjı sadece %{margin}. Fiyat artışı düşünebilirsiniz.",
                    "product_name": agg["product_name"],
                })
            # High return rate
            if agg["return_rate"] >= Decimal("15"):
                insights.append({
                    "type": "warning",
                    "title": "Yüksek İade Riski",
                    "message": f"\"{agg['product_name']}\" ürününün iade oranı %{agg['return_rate']}. Ürün kalitesi veya açıklamalarını kontrol edin.",
                    "product_name": agg["product_name"],
                })

        return Response({
            "kpis": kpis,
            "orders": paginated_rows,
            "hourly_performance": hourly_list,
            "product_heatmap": heatmap,
            "insights": insights,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
            }
        })

class ProductAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            org = request.user.profile.organization
        except Exception:
            return Response({"error": "Organizasyon bulunamadı"}, status=400)

        tz_istanbul = timezone.get_fixed_timezone(180)
        from datetime import datetime as dt_cls, time as dt_time, timedelta
        from collections import defaultdict

        # Accept both min_date/max_date and start_date/end_date for compatibility
        min_date_str = request.query_params.get("min_date") or request.query_params.get("start_date")
        max_date_str = request.query_params.get("max_date") or request.query_params.get("end_date")

        if min_date_str and max_date_str:
            try:
                min_date = dt_cls.strptime(min_date_str, "%Y-%m-%d").replace(tzinfo=tz_istanbul)
                max_date = dt_cls.combine(
                    dt_cls.strptime(max_date_str, "%Y-%m-%d").date(), dt_time.max
                ).replace(tzinfo=tz_istanbul)
            except ValueError:
                min_date = timezone.localtime(timezone.now() - timedelta(days=30), tz_istanbul)
                max_date = timezone.localtime(timezone.now(), tz_istanbul)
        else:
            min_date = timezone.localtime(timezone.now() - timedelta(days=30), tz_istanbul)
            max_date = timezone.localtime(timezone.now(), tz_istanbul)

        orders_qs = Order.objects.filter(
            organization=org,
            order_date__gte=min_date,
            order_date__lte=max_date,
        ).exclude(
            status__in=["Cancelled", "Returned", "UnSupplied"]
        ).prefetch_related(
            'items__product_variant__product',
            'items__transactions'
        ).select_related('marketplace_account').order_by('order_date')

        # Returned orders for return cargo loss calculation
        returned_qs = Order.objects.filter(
            organization=org,
            order_date__gte=min_date,
            order_date__lte=max_date,
            status="Returned",
        ).prefetch_related(
            'items__product_variant__product',
            'items__transactions'
        ).select_related('marketplace_account')

        product_agg = defaultdict(lambda: {
            "barcode": "",
            "title": "",
            "model_code": "",
            "category": "",
            "stock": 0,
            "total_sold_quantity": 0,
            "revenue": Decimal("0"),
            "net_profit": Decimal("0"),
            "return_cargo_loss": Decimal("0"),
            "commission": Decimal("0"),
            "cargo": Decimal("0"),
            "tax": Decimal("0"),
            "service_fee": Decimal("0"),
            "cost": Decimal("0"),
            "return_rate": Decimal("0"),
            "trend": defaultdict(lambda: {"revenue": Decimal("0"), "profit": Decimal("0")}),
        })

        for order in orders_qs:
            calc = ProfitCalculator.calculate_for_order(order)
            order_profit = calc["net_profit"]
            order_sale = calc["total_sale"]
            order_date_str = timezone.localtime(order.order_date, tz_istanbul).strftime("%Y-%m-%d")

            fi = order.items.first()
            if not fi or not fi.product_variant or not fi.product_variant.product:
                continue

            p = fi.product_variant.product
            v = fi.product_variant
            pk = p.barcode or p.marketplace_sku or p.title

            agg = product_agg[pk]
            if not agg["barcode"]:
                agg["barcode"] = pk
                agg["title"] = p.title
                agg["model_code"] = v.marketplace_sku or p.marketplace_sku or ""
                agg["category"] = p.category_name
                agg["stock"] = p.current_stock
                agg["return_rate"] = p.return_rate or Decimal("0")

            agg["total_sold_quantity"] += 1
            agg["revenue"] += order_sale
            agg["net_profit"] += order_profit

            agg["commission"] += calc["commission"]
            agg["cargo"] += calc["cargo"]
            agg["service_fee"] += calc["service_fee"]
            agg["tax"] += calc.get("kdv_detail", {}).get("net_kdv", Decimal("0"))
            agg["cost"] += calc["product_cost"] + calc.get("extra_product_cost", Decimal("0"))

            agg["trend"][order_date_str]["revenue"] += order_sale
            agg["trend"][order_date_str]["profit"] += order_profit

        # Accumulate return cargo loss from returned orders
        for order in returned_qs:
            fi = order.items.first()
            if not fi or not fi.product_variant or not fi.product_variant.product:
                continue

            p = fi.product_variant.product
            pk = p.barcode or p.marketplace_sku or p.title

            # Only add to existing products (don't create new entries for returns-only products)
            if pk in product_agg:
                calc = ProfitCalculator.calculate_for_order(order)
                cargo_loss = calc.get("cargo", Decimal("0"))
                product_agg[pk]["return_cargo_loss"] += cargo_loss

        max_sales = max([a["total_sold_quantity"] for a in product_agg.values()]) if product_agg else 1
        avg_sales = (sum([a["total_sold_quantity"] for a in product_agg.values()]) / len(product_agg)) if product_agg else 0

        results = []
        for pk, agg in product_agg.items():
            revenue = agg["revenue"]
            profit = agg["net_profit"]
            cost = agg["cost"]

            # Kâr Oranı = Kâr / Satış Tutarı × 100
            profit_rate = (profit / revenue * Decimal("100")) if revenue > 0 else Decimal("0")
            # Kâr Marjı = Kâr / Maliyet × 100
            profit_margin = (profit / cost * Decimal("100")) if cost > 0 else Decimal("0")

            return_rate_pct = agg["return_rate"]
            normalized_velocity = (Decimal(agg["total_sold_quantity"]) / Decimal(max_sales)) * Decimal("100")

            capped_margin = max(Decimal("0"), min(Decimal("100"), profit_rate))
            capped_return = max(Decimal("0"), min(Decimal("100"), return_rate_pct))

            score = (capped_margin * Decimal("0.4")) + (normalized_velocity * Decimal("0.3")) + ((Decimal("100") - capped_return) * Decimal("0.3"))
            score = max(Decimal("0"), min(score, Decimal("100"))).quantize(Decimal("0.1"))

            segment = "Standard"
            if profit > 0 and profit_rate > 15 and agg["total_sold_quantity"] > avg_sales:
                segment = "Cash Cow"
            elif profit > 0 and profit_rate <= 15 and agg["total_sold_quantity"] > avg_sales:
                segment = "Growth"
            elif profit <= 0 or agg["total_sold_quantity"] < (avg_sales * 0.2):
                segment = "Dead"

            tags = []
            if profit < 0: tags.append("Loss making")
            if 0 <= profit_rate < 10: tags.append("Low margin")
            if return_rate_pct > 10: tags.append("High return rate")
            if score >= 80: tags.append("Best performer")

            actions = []
            if segment == "Cash Cow" and agg["stock"] < 20: actions.append("Restock")
            if "Loss making" in tags or segment == "Growth": actions.append("Increase price")
            if segment == "Dead" and agg["stock"] > 50: actions.append("Stop selling")
            if score >= 70 and agg["stock"] > 10: actions.append("Increase ads")

            trend_arr = []
            for d in range(6, -1, -1):
                date_str = (timezone.localtime(timezone.now(), tz_istanbul) - timedelta(days=d)).strftime("%Y-%m-%d")
                t_data = agg["trend"].get(date_str, {"revenue": Decimal("0"), "profit": Decimal("0")})
                trend_arr.append({
                    "date": date_str,
                    "revenue": str(t_data["revenue"].quantize(Decimal("0.01"))),
                    "profit": str(t_data["profit"].quantize(Decimal("0.01")))
                })

            results.append({
                "barcode": agg["barcode"],
                "title": agg["title"],
                "model_code": agg["model_code"],
                "category": agg["category"],
                "stock": agg["stock"],
                "total_sold_quantity": agg["total_sold_quantity"],
                "total_sales_amount": str(revenue.quantize(Decimal("0.01"))),
                "total_profit": str(profit.quantize(Decimal("0.01"))),
                "return_cargo_loss": str(agg["return_cargo_loss"].quantize(Decimal("0.01"))),
                "profit_rate": str(profit_rate.quantize(Decimal("0.01"))),
                "profit_margin": str(profit_margin.quantize(Decimal("0.01"))),
                # Extra fields used by advanced analysis page
                "score": str(score),
                "segment": segment,
                "tags": tags,
                "actions": actions,
                "trend": trend_arr,
                "breakdown": {
                    "sale_price": str(revenue.quantize(Decimal("0.01"))),
                    "commission": str(agg["commission"].quantize(Decimal("0.01"))),
                    "cargo": str(agg["cargo"].quantize(Decimal("0.01"))),
                    "tax": str(agg["tax"].quantize(Decimal("0.01"))),
                    "return_loss": str(agg["return_cargo_loss"].quantize(Decimal("0.01"))),
                    "net_profit": str(profit.quantize(Decimal("0.01"))),
                }
            })

        results.sort(key=lambda x: Decimal(x["total_profit"]), reverse=True)
        return Response({"ok": True, "data": results})


class ProductProfitabilityExcelExportView(APIView):
    """
    GET /api/reports/product-profitability/export-excel/
    Ürün kârlılık verilerini Excel olarak dışa aktarır.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            org = request.user.profile.organization
        except Exception:
            return Response({"error": "Organizasyon bulunamadı"}, status=400)

        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment
        from io import BytesIO
        from django.http import HttpResponse
        from datetime import datetime as dt_cls, time as dt_time, timedelta
        from collections import defaultdict

        tz_istanbul = timezone.get_fixed_timezone(180)
        min_date_str = request.query_params.get("min_date") or request.query_params.get("start_date")
        max_date_str = request.query_params.get("max_date") or request.query_params.get("end_date")

        if min_date_str and max_date_str:
            try:
                min_date = dt_cls.strptime(min_date_str, "%Y-%m-%d").replace(tzinfo=tz_istanbul)
                max_date = dt_cls.combine(
                    dt_cls.strptime(max_date_str, "%Y-%m-%d").date(), dt_time.max
                ).replace(tzinfo=tz_istanbul)
            except ValueError:
                min_date = timezone.localtime(timezone.now() - timedelta(days=30), tz_istanbul)
                max_date = timezone.localtime(timezone.now(), tz_istanbul)
        else:
            min_date = timezone.localtime(timezone.now() - timedelta(days=30), tz_istanbul)
            max_date = timezone.localtime(timezone.now(), tz_istanbul)

        orders_qs = Order.objects.filter(
            organization=org,
            order_date__gte=min_date,
            order_date__lte=max_date,
        ).exclude(
            status__in=["Cancelled", "Returned", "UnSupplied"]
        ).prefetch_related(
            'items__product_variant__product',
            'items__transactions'
        ).select_related('marketplace_account').order_by('order_date')

        returned_qs = Order.objects.filter(
            organization=org,
            order_date__gte=min_date,
            order_date__lte=max_date,
            status="Returned",
        ).prefetch_related(
            'items__product_variant__product',
            'items__transactions'
        ).select_related('marketplace_account')

        product_agg = defaultdict(lambda: {
            "barcode": "",
            "title": "",
            "model_code": "",
            "category": "",
            "stock": 0,
            "total_sold_quantity": 0,
            "revenue": Decimal("0"),
            "net_profit": Decimal("0"),
            "return_cargo_loss": Decimal("0"),
            "cost": Decimal("0"),
        })

        for order in orders_qs:
            calc = ProfitCalculator.calculate_for_order(order)
            fi = order.items.first()
            if not fi or not fi.product_variant or not fi.product_variant.product:
                continue

            p = fi.product_variant.product
            v = fi.product_variant
            pk = p.barcode or p.marketplace_sku or p.title

            agg = product_agg[pk]
            if not agg["barcode"]:
                agg["barcode"] = pk
                agg["title"] = p.title
                agg["model_code"] = v.marketplace_sku or p.marketplace_sku or ""
                agg["category"] = p.category_name
                agg["stock"] = p.current_stock

            agg["total_sold_quantity"] += 1
            agg["revenue"] += calc["total_sale"]
            agg["net_profit"] += calc["net_profit"]
            agg["cost"] += calc["product_cost"] + calc.get("extra_product_cost", Decimal("0"))

        for order in returned_qs:
            fi = order.items.first()
            if not fi or not fi.product_variant or not fi.product_variant.product:
                continue
            p = fi.product_variant.product
            pk = p.barcode or p.marketplace_sku or p.title
            if pk in product_agg:
                calc = ProfitCalculator.calculate_for_order(order)
                product_agg[pk]["return_cargo_loss"] += calc.get("cargo", Decimal("0"))

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ürün Kârlılık"

        header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=10)
        profit_fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
        loss_fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")

        columns = [
            "Barkod", "Ürün Adı", "Stok", "Model Kodu", "Kategori",
            "Satış Adedi", "Satış Tutarı (₺)", "Kâr Tutarı (₺)",
            "İade Kargo Zararı (₺)", "Kâr Oranı (%)", "Kâr Marjı (%)",
        ]
        ws.append(columns)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 25

        col_widths = [18, 40, 8, 18, 20, 12, 18, 18, 20, 14, 14]
        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = w

        results = sorted(product_agg.values(), key=lambda x: x["net_profit"], reverse=True)
        for agg in results:
            revenue = agg["revenue"]
            profit = agg["net_profit"]
            cost = agg["cost"]
            profit_rate = float((profit / revenue * Decimal("100")).quantize(Decimal("0.01"))) if revenue > 0 else 0.0
            profit_margin = float((profit / cost * Decimal("100")).quantize(Decimal("0.01"))) if cost > 0 else 0.0

            row = [
                agg["barcode"],
                agg["title"],
                agg["stock"],
                agg["model_code"],
                agg["category"],
                agg["total_sold_quantity"],
                float(revenue.quantize(Decimal("0.01"))),
                float(profit.quantize(Decimal("0.01"))),
                float(agg["return_cargo_loss"].quantize(Decimal("0.01"))),
                profit_rate,
                profit_margin,
            ]
            ws.append(row)
            profit_cell = ws.cell(ws.max_row, 8)
            profit_cell.fill = profit_fill if profit >= 0 else loss_fill

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="Urun_Karliligi.xlsx"'
        return response
