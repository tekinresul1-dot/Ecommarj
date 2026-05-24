"""
Kargo Ayarları API Views.

GET/PATCH  /api/settings/cargo/              → Satıcı kargo ayarları
GET        /api/settings/cargo/companies/    → Aktif kargo firmaları
GET/PATCH  /api/settings/cargo/rates/        → Fiyat tablosu (pivot grid)
POST       /api/settings/cargo/rates/bulk-update/   → Toplu güncelleme
POST       /api/settings/cargo/rates/import/        → Excel/CSV import
POST       /api/settings/cargo/rates/reset-defaults/ → Varsayılana sıfırla
"""
import csv
import io
import logging
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    CargoCompany,
    CargoRate,
    CargoRateImportHistory,
    SellerCargoSettings,
    UserProfile,
    Organization,
)

logger = logging.getLogger(__name__)


def _get_org(user):
    """Kullanıcının organizasyonunu döner, yoksa oluşturur."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    org = profile.organization
    if not org:
        org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
        profile.organization = org
        profile.save(update_fields=["organization"])
    return org


def _normalize_price(val) -> Decimal:
    """
    Virgüllü / noktalı fiyat string'ini Decimal'e çevirir.
    83,93 → 83.93
    83.93 → 83.93
    """
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    s = str(val).strip().replace(" ", "")
    # Eğer hem virgül hem nokta varsa: 1.083,93 → 1083.93
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return Decimal(s)


# ═══════════════════════════════════════════════════════════════
# 1. Kargo Ayarları (Settings)
# ═══════════════════════════════════════════════════════════════

class CargoSettingsView(APIView):
    """GET/PATCH /api/settings/cargo/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = _get_org(request.user)
        settings_obj, _ = SellerCargoSettings.objects.get_or_create(organization=org)

        # Özet bilgileri
        active_company_count = CargoCompany.objects.filter(is_active=True).count()
        has_custom = CargoRate.objects.filter(organization=org).exists()
        desi_range = CargoRate.objects.filter(organization=org).values_list(
            "desi_kg", flat=True
        ).distinct().order_by("desi_kg")
        if not desi_range:
            desi_range = CargoRate.objects.filter(
                organization__isnull=True
            ).values_list("desi_kg", flat=True).distinct().order_by("desi_kg")

        return Response({
            "default_cargo_company": {
                "id": settings_obj.default_cargo_company_id,
                "name": settings_obj.default_cargo_company.name if settings_obj.default_cargo_company else None,
                "code": settings_obj.default_cargo_company.code if settings_obj.default_cargo_company else None,
            } if settings_obj.default_cargo_company else None,
            "use_order_cargo_company": settings_obj.use_order_cargo_company,
            "use_default_if_missing": settings_obj.use_default_if_missing,
            "apply_barem_0_199": settings_obj.apply_barem_0_199,
            "apply_barem_200_349": settings_obj.apply_barem_200_349,
            "custom_note": settings_obj.custom_note,
            "active_company_count": active_company_count,
            "has_custom_rates": has_custom,
            "desi_range": list(desi_range),
            "last_updated": settings_obj.updated_at.isoformat(),
        })

    def patch(self, request):
        org = _get_org(request.user)
        settings_obj, _ = SellerCargoSettings.objects.get_or_create(organization=org)
        data = request.data

        if "default_cargo_company_id" in data:
            cid = data["default_cargo_company_id"]
            if cid:
                try:
                    company = CargoCompany.objects.get(id=cid, is_active=True)
                    settings_obj.default_cargo_company = company
                except CargoCompany.DoesNotExist:
                    return Response({"error": "Geçersiz kargo firması."}, status=400)
            else:
                settings_obj.default_cargo_company = None

        for field in [
            "use_order_cargo_company",
            "use_default_if_missing",
            "apply_barem_0_199",
            "apply_barem_200_349",
        ]:
            if field in data:
                setattr(settings_obj, field, bool(data[field]))

        if "custom_note" in data:
            settings_obj.custom_note = str(data["custom_note"])[:1000]

        settings_obj.save()
        return Response({"message": "Kargo ayarları güncellendi."})


# ═══════════════════════════════════════════════════════════════
# 2. Kargo Firmaları
# ═══════════════════════════════════════════════════════════════

class CargoCompanyListView(APIView):
    """GET /api/settings/cargo/companies/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = CargoCompany.objects.filter(is_active=True).values(
            "id", "name", "code"
        ).order_by("name")
        return Response({"companies": list(companies)})


# ═══════════════════════════════════════════════════════════════
# 3. Fiyat Tablosu (Pivot Grid)
# ═══════════════════════════════════════════════════════════════

class CargoRateView(APIView):
    """GET/PATCH /api/settings/cargo/rates/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = _get_org(request.user)
        companies = list(
            CargoCompany.objects.filter(is_active=True).order_by("name").values("id", "name", "code")
        )

        # Satıcının özel fiyatları varsa onları getir, yoksa global
        has_custom = CargoRate.objects.filter(organization=org).exists()
        if has_custom:
            rates_qs = CargoRate.objects.filter(
                organization=org, is_active=True
            ).select_related("cargo_company")
        else:
            rates_qs = CargoRate.objects.filter(
                organization__isnull=True, is_active=True
            ).select_related("cargo_company")

        # Pivot: desi → {firma_name: fiyat, ...}
        pivot = {}
        for rate in rates_qs:
            if rate.desi_kg not in pivot:
                pivot[rate.desi_kg] = {"desi_kg": rate.desi_kg}
            pivot[rate.desi_kg][rate.cargo_company.name] = float(rate.price)

        rates = sorted(pivot.values(), key=lambda r: r["desi_kg"])

        last_rate = rates_qs.order_by("-updated_at").first()
        last_updated = last_rate.updated_at.isoformat() if last_rate else None

        return Response({
            "companies": [c["name"] for c in companies],
            "company_details": companies,
            "rates": rates,
            "has_custom_rates": has_custom,
            "last_updated": last_updated,
        })

    def patch(self, request):
        """Toplu fiyat güncelleme: [{company_name, desi_kg, price}, ...]"""
        org = _get_org(request.user)
        updates = request.data.get("updates", [])

        if not updates:
            return Response({"error": "Güncellenecek veri yok."}, status=400)

        # Eğer satıcının özel tablosu yoksa, global'den kopyala
        if not CargoRate.objects.filter(organization=org).exists():
            self._copy_global_to_org(org)

        errors = []
        updated = 0

        with transaction.atomic():
            for item in updates:
                company_name = item.get("company_name")
                desi_kg = item.get("desi_kg")
                raw_price = item.get("price")

                try:
                    price = _normalize_price(raw_price)
                    if price < 0:
                        errors.append(f"Desi {desi_kg} / {company_name}: Negatif fiyat.")
                        continue
                except (InvalidOperation, ValueError):
                    errors.append(f"Desi {desi_kg} / {company_name}: Geçersiz fiyat '{raw_price}'.")
                    continue

                try:
                    company = CargoCompany.objects.get(name=company_name)
                except CargoCompany.DoesNotExist:
                    errors.append(f"Bilinmeyen firma: {company_name}")
                    continue

                CargoRate.objects.update_or_create(
                    organization=org,
                    cargo_company=company,
                    desi_kg=desi_kg,
                    defaults={"price": price, "is_active": True},
                )
                updated += 1

        return Response({
            "message": f"{updated} fiyat güncellendi.",
            "errors": errors,
            "updated_count": updated,
        })

    @staticmethod
    def _copy_global_to_org(org):
        """Global fiyat tablosunu satıcıya kopyalar."""
        global_rates = CargoRate.objects.filter(
            organization__isnull=True, is_active=True
        )
        bulk = []
        for gr in global_rates:
            bulk.append(CargoRate(
                organization=org,
                cargo_company=gr.cargo_company,
                desi_kg=gr.desi_kg,
                price=gr.price,
                is_active=True,
            ))
        if bulk:
            CargoRate.objects.bulk_create(bulk, ignore_conflicts=True)


# ═══════════════════════════════════════════════════════════════
# 4. Toplu Güncelleme (Yüzde / Sabit Tutar)
# ═══════════════════════════════════════════════════════════════

class CargoBulkUpdateView(APIView):
    """POST /api/settings/cargo/rates/bulk-update/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org = _get_org(request.user)
        data = request.data

        company_name = data.get("company_name")
        desi_start = int(data.get("desi_start", 1))
        desi_end = int(data.get("desi_end", 20))
        update_type = data.get("update_type")  # "percent" | "fixed" | "set"
        value = _normalize_price(data.get("value", "0"))

        if not company_name:
            return Response({"error": "Kargo firması seçilmedi."}, status=400)

        try:
            company = CargoCompany.objects.get(name=company_name)
        except CargoCompany.DoesNotExist:
            return Response({"error": f"Firma bulunamadı: {company_name}"}, status=400)

        # Satıcının özel tablosu yoksa global'den kopyala
        if not CargoRate.objects.filter(organization=org).exists():
            CargoRateView._copy_global_to_org(org)

        rates = CargoRate.objects.filter(
            organization=org,
            cargo_company=company,
            desi_kg__gte=desi_start,
            desi_kg__lte=desi_end,
        )

        updated = 0
        with transaction.atomic():
            for rate in rates:
                if update_type == "percent":
                    # +10 → %10 zam, -5 → %5 indirim
                    rate.price = (rate.price * (Decimal("1") + value / Decimal("100"))).quantize(Decimal("0.01"))
                elif update_type == "fixed":
                    # +5 → 5 TL ekle, -3 → 3 TL çıkar
                    rate.price = rate.price + value
                elif update_type == "set":
                    # Doğrudan yeni fiyat
                    rate.price = value
                else:
                    continue

                if rate.price < 0:
                    rate.price = Decimal("0.00")

                rate.save(update_fields=["price", "updated_at"])
                updated += 1

        return Response({
            "message": f"{company_name} — {desi_start}-{desi_end} desi: {updated} fiyat güncellendi.",
            "updated_count": updated,
        })


# ═══════════════════════════════════════════════════════════════
# 5. Excel / CSV Import
# ═══════════════════════════════════════════════════════════════

COMPANY_NAME_MAP = {
    "aras": "Aras Kargo",
    "aras kargo": "Aras Kargo",
    "dhl": "DHL eCommerce",
    "dhl ecommerce": "DHL eCommerce",
    "kolay gelsin": "Kolay Gelsin",
    "kolaygelsin": "Kolay Gelsin",
    "ptt": "PTT Kargo",
    "ptt kargo": "PTT Kargo",
    "sürat": "Sürat Kargo",
    "surat": "Sürat Kargo",
    "sürat kargo": "Sürat Kargo",
    "tex": "Trendyol Express",
    "trendyol express": "Trendyol Express",
    "yurtiçi": "Yurtiçi Kargo",
    "yurtici": "Yurtiçi Kargo",
    "yurtiçi kargo": "Yurtiçi Kargo",
    "yurtici kargo": "Yurtiçi Kargo",
    "ceva tedarik": "CEVA Tedarik",
    "cevatedarik": "CEVA Tedarik",
    "ceva": "CEVA",
    "horoz": "Horoz Lojistik",
    "horoz lojistik": "Horoz Lojistik",
}


class CargoRateImportView(APIView):
    """POST /api/settings/cargo/rates/import/"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        org = _get_org(request.user)
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "Dosya yüklenmedi."}, status=400)

        file_name = file.name.lower()
        if not (file_name.endswith(".csv") or file_name.endswith(".xlsx") or file_name.endswith(".xls")):
            return Response({"error": "Sadece CSV veya Excel dosyaları desteklenir."}, status=400)

        try:
            if file_name.endswith(".csv"):
                rows = self._parse_csv(file)
            else:
                rows = self._parse_excel(file)
        except Exception as e:
            return Response({"error": f"Dosya okunurken hata: {str(e)}"}, status=400)

        if not rows:
            return Response({"error": "Dosyada veri bulunamadı."}, status=400)

        # Preview mode
        preview = request.data.get("preview", "true").lower() == "true"
        if preview:
            return Response({
                "preview": True,
                "rows": rows[:25],
                "total_rows": len(rows),
                "file_name": file.name,
            })

        # Import mode
        imported, failed, errors = self._import_rows(org, rows)

        history_status = "success"
        if failed > 0 and imported > 0:
            history_status = "partial"
        elif failed > 0 and imported == 0:
            history_status = "failed"

        CargoRateImportHistory.objects.create(
            organization=org,
            file_name=file.name,
            imported_rows=imported,
            failed_rows=failed,
            status=history_status,
            error_message="\n".join(errors[:20]),
        )

        return Response({
            "preview": False,
            "imported_rows": imported,
            "failed_rows": failed,
            "errors": errors[:20],
            "status": history_status,
        })

    def _parse_csv(self, file):
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content), delimiter=";")
        if not reader.fieldnames:
            reader = csv.DictReader(io.StringIO(content), delimiter=",")
        return list(reader)

    def _parse_excel(self, file):
        try:
            import openpyxl
        except ImportError:
            raise Exception("Excel desteği için openpyxl gerekli.")

        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = next(rows_iter)
        headers = [str(h).strip() if h else "" for h in headers]
        result = []
        for row in rows_iter:
            if not any(row):
                continue
            result.append({headers[i]: row[i] for i in range(len(headers)) if i < len(row)})
        return result

    def _import_rows(self, org, rows):
        imported = 0
        failed = 0
        errors = []

        # İlk satırın anahtarlarından firma isimlerini çıkar
        if not rows:
            return 0, 0, ["Boş dosya"]

        company_cache = {}
        for c in CargoCompany.objects.filter(is_active=True):
            company_cache[c.name.lower()] = c

        with transaction.atomic():
            for row_idx, row in enumerate(rows, start=2):
                desi_key = None
                for k in row.keys():
                    kl = k.lower().strip()
                    if kl in ("desi", "desi/kg", "desi_kg", "kg", "desi / kg"):
                        desi_key = k
                        break

                if not desi_key:
                    errors.append(f"Satır {row_idx}: Desi/KG kolonu bulunamadı.")
                    failed += 1
                    continue

                try:
                    desi = int(float(str(row[desi_key]).replace(",", ".")))
                except (ValueError, TypeError):
                    errors.append(f"Satır {row_idx}: Geçersiz desi değeri '{row[desi_key]}'.")
                    failed += 1
                    continue

                for col_name, raw_val in row.items():
                    if col_name == desi_key:
                        continue
                    if raw_val is None or str(raw_val).strip() == "":
                        continue

                    normalized = COMPANY_NAME_MAP.get(col_name.lower().strip())
                    if normalized:
                        company = company_cache.get(normalized.lower())
                    else:
                        company = company_cache.get(col_name.lower().strip())

                    if not company:
                        continue  # Bilinmeyen kolon — skip

                    try:
                        price = _normalize_price(raw_val)
                        if price < 0:
                            errors.append(f"Satır {row_idx}, {company.name}: Negatif fiyat.")
                            failed += 1
                            continue
                    except (InvalidOperation, ValueError):
                        errors.append(f"Satır {row_idx}, {company.name}: Geçersiz fiyat '{raw_val}'.")
                        failed += 1
                        continue

                    CargoRate.objects.update_or_create(
                        organization=org,
                        cargo_company=company,
                        desi_kg=desi,
                        defaults={"price": price, "is_active": True},
                    )
                    imported += 1

        return imported, failed, errors


# ═══════════════════════════════════════════════════════════════
# 6. Varsayılana Sıfırla
# ═══════════════════════════════════════════════════════════════

class CargoRateResetView(APIView):
    """POST /api/settings/cargo/rates/reset-defaults/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org = _get_org(request.user)

        # Satıcının mevcut özel fiyatlarını sil
        deleted_count, _ = CargoRate.objects.filter(organization=org).delete()

        # Global fiyatları satıcıya kopyala
        global_rates = CargoRate.objects.filter(
            organization__isnull=True, is_active=True
        )
        bulk = []
        for gr in global_rates:
            bulk.append(CargoRate(
                organization=org,
                cargo_company=gr.cargo_company,
                desi_kg=gr.desi_kg,
                price=gr.price,
                is_active=True,
            ))
        created_count = 0
        if bulk:
            CargoRate.objects.bulk_create(bulk, ignore_conflicts=True)
            created_count = len(bulk)

        return Response({
            "message": f"Varsayılan fiyatlar yüklendi. {deleted_count} eski kayıt silindi, {created_count} yeni fiyat oluşturuldu.",
            "deleted_count": deleted_count,
            "created_count": created_count,
        })
