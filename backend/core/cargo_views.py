"""
Kargo Ayarları API Views.

GET/PATCH  /api/settings/cargo/                     → Satıcı kargo ayarları
GET        /api/settings/cargo/companies/           → Aktif kargo firmaları (dropdown için)
GET        /api/settings/cargo/custom-rates/        → Özel desi listesi
POST       /api/settings/cargo/custom-rates/import/ → Excel yükle
DELETE     /api/settings/cargo/custom-rates/reset/  → Özel fiyatları sıfırla
GET        /api/settings/cargo/template/            → Excel şablonu indir
"""
import csv
import io
import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    CargoCompany,
    SellerCargoSettings,
    SellerCustomCargoRate,
    CargoRateUpload,
    UserProfile,
    Organization,
)

logger = logging.getLogger(__name__)

def _get_org(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    org = profile.organization
    if not org:
        org, _ = Organization.objects.get_or_create(name=f"{user.username} Organizasyonu")
        profile.organization = org
        profile.save(update_fields=["organization"])
    return org

def _normalize_price(val) -> Decimal:
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    s = str(val).strip().replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return Decimal(s)

class CargoSettingsView(APIView):
    """GET/PATCH /api/settings/cargo/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = _get_org(request.user)
        settings_obj, _ = SellerCargoSettings.objects.get_or_create(organization=org)
        
        return Response({
            "default_cargo_company_id": settings_obj.default_cargo_company_id,
            "use_trendyol_real_cargo_if_available": settings_obj.use_trendyol_real_cargo_if_available,
            "use_custom_cargo_rates": settings_obj.use_custom_cargo_rates,
            "apply_barem_discount_0_199": settings_obj.apply_barem_discount_0_199,
            "apply_barem_discount_200_349": settings_obj.apply_barem_discount_200_349,
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
            "use_trendyol_real_cargo_if_available",
            "use_custom_cargo_rates",
            "apply_barem_discount_0_199",
            "apply_barem_discount_200_349",
        ]:
            if field in data:
                setattr(settings_obj, field, bool(data[field]))

        settings_obj.save()
        return Response({"message": "Kargo ayarları güncellendi."})


class CargoCompanyListView(APIView):
    """GET /api/settings/cargo/companies/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = CargoCompany.objects.filter(is_active=True).values(
            "id", "name", "code"
        ).order_by("name")
        return Response({"companies": list(companies)})


class CustomCargoRateListView(APIView):
    """GET /api/settings/cargo/custom-rates/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        org = _get_org(request.user)
        rates = SellerCustomCargoRate.objects.filter(
            organization=org, is_active=True
        ).order_by("desi")
        
        last_upload = CargoRateUpload.objects.filter(organization=org, status="success").order_by("-uploaded_at").first()
        
        data = [
            {
                "id": r.id,
                "desi": r.desi,
                "price": r.price_vat_included,
                "currency": r.currency,
                "source": r.source,
                "updated_at": r.updated_at.isoformat(),
            } for r in rates
        ]
        
        return Response({
            "rates": data,
            "last_upload_date": last_upload.uploaded_at.isoformat() if last_upload else None,
            "has_custom_rates": len(data) > 0
        })

class CustomCargoRateImportView(APIView):
    """POST /api/settings/cargo/custom-rates/import/"""
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

        imported, failed, errors = self._import_rows(org, rows)

        history_status = "success"
        if failed > 0 and imported > 0:
            history_status = "partial"
        elif failed > 0 and imported == 0:
            history_status = "failed"

        CargoRateUpload.objects.create(
            organization=org,
            file_name=file.name,
            row_count=len(rows),
            valid_row_count=imported,
            failed_row_count=failed,
            status=history_status,
            error_message="\n".join(errors[:20]),
        )
        
        if imported > 0:
            settings_obj, _ = SellerCargoSettings.objects.get_or_create(organization=org)
            settings_obj.use_custom_cargo_rates = True
            settings_obj.save(update_fields=["use_custom_cargo_rates"])

        return Response({
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
        
        headers = None
        for row in rows_iter:
            # Check if this row contains our expected headers
            row_strs = [str(cell).strip().lower() for cell in row if cell is not None]
            if "desi" in row_strs or "desi_kg" in row_strs or "desi/kg" in row_strs:
                headers = [str(h).strip() if h else "" for h in row]
                break
                
        if not headers:
            raise Exception("Excel dosyasında başlık satırı ('Desi' vs.) bulunamadı.")
            
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

        if not rows:
            return 0, 0, ["Boş dosya"]

        first_row = rows[0]
        desi_key = None
        price_key = None
        
        for k in first_row.keys():
            kl = str(k).lower().strip()
            if kl in ("desi", "desi/kg", "desi_kg", "kg"):
                desi_key = k
            elif kl in ("kargo fiyatı", "fiyat", "price", "kargo fiyatı (kdv dahil)"):
                price_key = k
                
        if not desi_key:
            return 0, len(rows), ["Dosyada 'Desi' kolonu bulunamadı."]
            
        if not price_key:
            for k in first_row.keys():
                if "fiyat" in str(k).lower():
                    price_key = k
                    break
        
        if not price_key:
             return 0, len(rows), ["Dosyada 'Fiyat' kolonu bulunamadı."]

        import uuid
        batch_id = f"batch_{org.id}_{uuid.uuid4().hex[:8]}"

        with transaction.atomic():
            SellerCustomCargoRate.objects.filter(organization=org, is_active=True).update(is_active=False)
            
            for row_idx, row in enumerate(rows, start=2):
                try:
                    desi_val = row.get(desi_key)
                    if desi_val is None or str(desi_val).strip() == "":
                        continue
                    desi = int(float(str(desi_val).replace(",", ".")))
                except (ValueError, TypeError):
                    errors.append(f"Satır {row_idx}: Geçersiz desi değeri '{row.get(desi_key)}'.")
                    failed += 1
                    continue
                    
                raw_price = row.get(price_key)
                if raw_price is None or str(raw_price).strip() == "":
                    continue
                    
                try:
                    price = _normalize_price(raw_price)
                    if price < 0:
                        errors.append(f"Satır {row_idx}, Desi {desi}: Negatif fiyat.")
                        failed += 1
                        continue
                except (InvalidOperation, ValueError):
                    errors.append(f"Satır {row_idx}, Desi {desi}: Geçersiz fiyat '{raw_price}'.")
                    failed += 1
                    continue

                SellerCustomCargoRate.objects.update_or_create(
                    organization=org,
                    desi=desi,
                    defaults={
                        "price_vat_included": price,
                        "is_active": True,
                        "upload_batch_id": batch_id,
                        "source": "uploaded_excel"
                    },
                )
                imported += 1

        return imported, failed, errors


class CustomCargoRateResetView(APIView):
    """DELETE /api/settings/cargo/custom-rates/reset/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        org = _get_org(request.user)
        deleted_count, _ = SellerCustomCargoRate.objects.filter(organization=org).delete()
        
        settings_obj, _ = SellerCargoSettings.objects.get_or_create(organization=org)
        if settings_obj.use_custom_cargo_rates:
            settings_obj.use_custom_cargo_rates = False
            settings_obj.save(update_fields=["use_custom_cargo_rates"])
            
        return Response({
            "message": f"Özel kargo fiyatları sıfırlandı. {deleted_count} kayıt silindi."
        })


class CargoTemplateDownloadView(APIView):
    """GET /api/settings/cargo/template/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Kargo Fiyatları"
        
        # Row 1 and 2: Instruction text
        instruction = "Anlaşmalı olduğunuz kargo firmasının desi fiyatlarını tablodan girebilirsiniz. Boş bırakılan desilerde Trendyol anlaşmalı kargo fiyatları baz alınacaktır."
        ws.merge_cells("A1:B2")
        cell_instr = ws["A1"]
        cell_instr.value = instruction
        cell_instr.font = Font(color="FF0000", bold=True)
        cell_instr.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Row 4: Headers
        headers = ["Desi", "Kargo Fiyatı (KDV Dahil)"]
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="F4CCCC", end_color="F4CCCC", fill_type="solid")
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            
        # Rows 5 to 104: Desi 1 to 100
        for i in range(1, 101):
            cell_desi = ws.cell(row=4+i, column=1)
            cell_desi.value = i
            cell_desi.alignment = Alignment(horizontal="right")
            
        # Adjust column widths
        ws.column_dimensions["A"].width = 15
        ws.column_dimensions["B"].width = 30
        
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="kargo_sablonu.xlsx"'
        wb.save(response)
        return response
