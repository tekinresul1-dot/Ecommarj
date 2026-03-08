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
        
        products = Product.objects.filter(
            organization=org,
            is_active=True
        ).prefetch_related('variants').order_by(
            django_models.F('trendyol_created_at').desc(nulls_last=True)
        ).distinct()
        
        search = request.GET.get('search', '').strip()
        if search:
            products = products.filter(
                Q(title__icontains=search) |
                Q(barcode__icontains=search) |
                Q(variants__barcode__icontains=search) |
                Q(variants__title__icontains=search)
            ).distinct()
            
        paginator = PageNumberPagination()
        paginator.page_size = 50
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100
        
        paginated_products = paginator.paginate_queryset(products, request)
        
        # Simple serialization
        data = []
        for p in paginated_products:
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
        
        # Sadece bu organizasyona ait olan siparişleri getir
        # prefetch_related ile db call optimizasyonu
        orders = Order.objects.filter(marketplace_account__organization=org).prefetch_related('items__product_variant__product', 'items__transactions').order_by('-order_date')
        
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
                commission_rate = item.applied_commission_rate or Decimal("0.00")
                image_url = ""
                if item.product_variant and item.product_variant.product:
                    title = item.product_variant.product.title
                    barcode = item.product_variant.barcode
                    image_url = item.product_variant.product.image_url or ""
                    if commission_rate == Decimal("0.00"):
                        commission_rate = item.product_variant.product.commission_rate
                
                items_data.append({
                    "id": item.id,
                    "title": title,
                    "barcode": barcode,
                    "quantity": item.quantity,
                    "sale_price_gross": str(item.sale_price_gross),
                    "commission_rate": str(commission_rate),
                    "image_url": image_url,
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
                "order_number": order.order_number,
                "order_date": format_date_tr(order.order_date),
                "status": order.status,
                "is_micro_export": order.channel == 'micro_export',
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
                    "stock": variant.product.current_stock or 0,
                    "model_code": variant.product.marketplace_sku or "",
                    "category": variant.product.category_name or "",
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
    Generates and returns an Excel file of products and variants.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from core.models import UserProfile, Organization, Product
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization

        products = Product.objects.filter(organization=org, is_active=True).prefetch_related('variants')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ürün Maliyetleri"

        headers = [
            "Barkod", "Model Kodu", "Stok kodu", "Kategori İsmi", "Ürün Adı", 
            "Trendyol Satış Fiyatı", "Stok", "Ürün Maliyeti ( KDV Dahil)", 
            "Maliyet KDV Oranı", "Para Birimi", "Ürün Desisi", "Bugün Kargoda Etiketi", 
            "Ekstra Maliyet (%)", "Ekstra Maliyet (TL)"
        ]

        header_fill = PatternFill(start_color="FDE9D9", end_color="FDE9D9", fill_type="solid")
        header_font = Font(bold=True)
        yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        teal_fill = PatternFill(start_color="008080", end_color="008080", fill_type="solid")
        teal_font = Font(bold=True, color="FFFFFF")

        for col_num, header_title in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header_title)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            if "Maliyet" in header_title or "KDV " in header_title or "Para Birimi" in header_title or "Desisi" in header_title or "Bugün Kargo" in header_title:
                if "Ekstra" in header_title:
                    cell.fill = teal_fill
                    cell.font = teal_font
                else:
                    cell.fill = yellow_fill
            else:
                cell.fill = header_fill

        row_num = 2
        for product in products:
            for variant in product.variants.all():
                ws.cell(row=row_num, column=1, value=variant.barcode)
                ws.cell(row=row_num, column=2, value=product.marketplace_sku)
                ws.cell(row=row_num, column=3, value=variant.marketplace_sku or product.marketplace_sku)
                ws.cell(row=row_num, column=4, value=product.category_name)
                ws.cell(row=row_num, column=5, value=variant.title or product.title)
                ws.cell(row=row_num, column=6, value=float(product.sale_price))
                ws.cell(row=row_num, column=7, value=product.current_stock)
                
                # Editable fields
                ws.cell(row=row_num, column=8, value=float(variant.cost_price))
                ws.cell(row=row_num, column=9, value=float(variant.cost_vat_rate))
                ws.cell(row=row_num, column=10, value="TRY")
                ws.cell(row=row_num, column=11, value=float(variant.desi) if variant.desi is not None else float(product.desi))
                ws.cell(row=row_num, column=12, value="Evet" if product.fast_delivery else "Hayır")
                ws.cell(row=row_num, column=13, value=0) # Ekstra Maliyet (%) placeholders
                ws.cell(row=row_num, column=14, value=0) # Ekstra Maliyet (TL) placeholders
                
                row_num += 1

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = min(adjusted_width, 50)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Urun_Maliyetleri.xlsx"'
        wb.save(response)
        return response


class ProductExcelImportView(APIView):
    """
    POST /api/products/import-excel/
    Parses uploaded Excel file to update Product and ProductVariant costs, vat, desi etc.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        from core.models import UserProfile, Organization, ProductVariant
        from decimal import Decimal
        
        profile, _ = UserProfile.objects.get_or_create(user=user)
        org = profile.organization

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Dosya bulunamadı."}, status=400)

        if not file.name.endswith('.xlsx') and not file.name.endswith('.xls'):
            return Response({"error": "Geçersiz dosya formatı. Lütfen .xlsx veya .xls yükleyin."}, status=400)

        try:
            wb = openpyxl.load_workbook(file, data_only=True)
            ws = wb.active
            
            headers = {}
            for index, cell in enumerate(ws[1]):
                if cell.value:
                    headers[str(cell.value).strip()] = index

            # Required headers check
            required_cols = ["Barkod", "Ürün Maliyeti ( KDV Dahil)", "Maliyet KDV Oranı"]
            if not all(col in headers for col in required_cols):
                 return Response({"error": f"Eksik sütunlar. Excel dosyanızda şu sütunlar olmalı: {', '.join(required_cols)}"}, status=400)

            updated_variants = 0
            
            # Map index
            idx_barkod = headers["Barkod"]
            idx_cost = headers["Ürün Maliyeti ( KDV Dahil)"]
            idx_vat = headers["Maliyet KDV Oranı"]
            idx_desi = headers.get("Ürün Desisi")
            idx_fast = headers.get("Bugün Kargoda Etiketi")

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[idx_barkod]:
                    continue
                    
                barcode = str(row[idx_barkod]).strip()
                try:
                    variant = ProductVariant.objects.select_related('product').get(barcode=barcode, product__organization=org)
                except ProductVariant.DoesNotExist:
                    continue # Skip variants not found or belonging to others
                    
                try:
                    # Update cost fields
                    cost_val = row[idx_cost]
                    vat_val = row[idx_vat]
                    
                    if cost_val is not None:
                        variant.cost_price = Decimal(str(cost_val).replace(',', '.'))
                    if vat_val is not None:
                        variant.cost_vat_rate = Decimal(str(vat_val).replace(',', '.'))
                        
                    # Update Desi
                    if idx_desi is not None and row[idx_desi] is not None:
                         desi_val = Decimal(str(row[idx_desi]).replace(',', '.'))
                         variant.desi = desi_val
                         # Optional: also update parent product desi if you'd like it globally synced
                         variant.product.desi = desi_val
                         
                    # Update fast delivery flag on parent
                    if idx_fast is not None and row[idx_fast] is not None:
                         fast_str = str(row[idx_fast]).strip().lower()
                         variant.product.fast_delivery = (fast_str == "evet")
                         
                    variant.product.save()
                    variant.save()
                    updated_variants += 1

                except Exception as e:
                    # Log error for specific row but continue processing others
                    print(f"Error processing row with barcode {barcode}: {e}")
                    pass
            
            return Response({"ok": True, "message": f"{updated_variants} ürün/varyant başarıyla güncellendi."})

        except Exception as e:
            return Response({"error": f"Excel dosyası okunamadı: {str(e)}"}, status=500)
