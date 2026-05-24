"""
Kargo firmalarını ve varsayılan desi fiyat tablosunu oluşturur.

Kullanım:
    python manage.py seed_cargo_companies
    python manage.py seed_cargo_companies --reset   # Mevcut global fiyatları sıfırla
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from core.models import CargoCompany, CargoRate


# ─────────────────────────────────────────────────────────────
# Kargo Firmaları
# ─────────────────────────────────────────────────────────────
COMPANIES = [
    {"name": "Aras Kargo",      "code": "aras"},
    {"name": "DHL eCommerce",   "code": "dhl"},
    {"name": "Kolay Gelsin",    "code": "kolaygelsin"},
    {"name": "PTT Kargo",       "code": "ptt"},
    {"name": "Sürat Kargo",     "code": "surat"},
    {"name": "Trendyol Express","code": "tex"},
    {"name": "Yurtiçi Kargo",   "code": "yurtici"},
    {"name": "CEVA Tedarik",    "code": "cevatedarik"},
    {"name": "CEVA",            "code": "ceva"},
    {"name": "Horoz Lojistik",  "code": "horoz"},
]

# ─────────────────────────────────────────────────────────────
# Varsayılan KDV Dahil Desi Fiyatları (TL)
# Trendyol Mart 2026 tarifesi baz alınmıştır.
# Desi: 1–20 arası
# ─────────────────────────────────────────────────────────────
#                         Aras    DHL     Kolay   PTT     Sürat   TEX     Yurtiçi  CEVAT   CEVA    Horoz
DEFAULT_RATES = {
    1:  [Decimal("51.49"), Decimal("62.50"), Decimal("61.49"), Decimal("41.00"), Decimal("58.49"), Decimal("41.00"), Decimal("89.50"), Decimal("55.00"), Decimal("52.00"), Decimal("50.00")],
    2:  [Decimal("57.24"), Decimal("66.00"), Decimal("65.49"), Decimal("45.50"), Decimal("62.49"), Decimal("45.50"), Decimal("95.50"), Decimal("60.00"), Decimal("57.00"), Decimal("55.00")],
    3:  [Decimal("62.99"), Decimal("69.50"), Decimal("69.49"), Decimal("50.00"), Decimal("66.49"), Decimal("50.00"), Decimal("101.50"), Decimal("65.00"), Decimal("62.00"), Decimal("60.00")],
    4:  [Decimal("68.74"), Decimal("73.00"), Decimal("73.49"), Decimal("54.50"), Decimal("70.49"), Decimal("54.50"), Decimal("107.50"), Decimal("70.00"), Decimal("67.00"), Decimal("65.00")],
    5:  [Decimal("74.49"), Decimal("76.50"), Decimal("77.49"), Decimal("59.00"), Decimal("74.49"), Decimal("59.00"), Decimal("113.50"), Decimal("75.00"), Decimal("72.00"), Decimal("70.00")],
    6:  [Decimal("80.24"), Decimal("80.00"), Decimal("81.49"), Decimal("63.50"), Decimal("78.49"), Decimal("63.50"), Decimal("119.50"), Decimal("80.00"), Decimal("77.00"), Decimal("75.00")],
    7:  [Decimal("85.99"), Decimal("83.50"), Decimal("85.49"), Decimal("68.00"), Decimal("82.49"), Decimal("68.00"), Decimal("125.50"), Decimal("85.00"), Decimal("82.00"), Decimal("80.00")],
    8:  [Decimal("88.50"), Decimal("85.80"), Decimal("87.90"), Decimal("72.50"), Decimal("86.49"), Decimal("72.50"), Decimal("129.50"), Decimal("88.00"), Decimal("85.00"), Decimal("83.00")],
    9:  [Decimal("91.74"), Decimal("88.40"), Decimal("90.49"), Decimal("77.00"), Decimal("90.49"), Decimal("77.00"), Decimal("133.50"), Decimal("91.00"), Decimal("88.00"), Decimal("86.00")],
    10: [Decimal("96.00"), Decimal("91.00"), Decimal("93.50"), Decimal("81.50"), Decimal("93.00"), Decimal("81.50"), Decimal("135.32"), Decimal("94.00"), Decimal("91.00"), Decimal("89.00")],
    11: [Decimal("100.50"), Decimal("94.00"), Decimal("97.00"), Decimal("86.00"), Decimal("96.50"), Decimal("86.00"), Decimal("140.00"), Decimal("98.00"), Decimal("95.00"), Decimal("93.00")],
    12: [Decimal("105.00"), Decimal("97.00"), Decimal("100.50"), Decimal("90.50"), Decimal("100.00"), Decimal("90.50"), Decimal("145.00"), Decimal("102.00"), Decimal("99.00"), Decimal("97.00")],
    13: [Decimal("109.50"), Decimal("100.00"), Decimal("104.00"), Decimal("95.00"), Decimal("103.50"), Decimal("95.00"), Decimal("150.00"), Decimal("106.00"), Decimal("103.00"), Decimal("101.00")],
    14: [Decimal("114.00"), Decimal("103.00"), Decimal("107.50"), Decimal("99.50"), Decimal("107.00"), Decimal("99.50"), Decimal("155.00"), Decimal("110.00"), Decimal("107.00"), Decimal("105.00")],
    15: [Decimal("118.50"), Decimal("106.00"), Decimal("111.00"), Decimal("104.00"), Decimal("110.50"), Decimal("104.00"), Decimal("160.00"), Decimal("114.00"), Decimal("111.00"), Decimal("109.00")],
    16: [Decimal("123.00"), Decimal("109.00"), Decimal("114.50"), Decimal("108.50"), Decimal("114.00"), Decimal("108.50"), Decimal("165.00"), Decimal("118.00"), Decimal("115.00"), Decimal("113.00")],
    17: [Decimal("127.50"), Decimal("112.00"), Decimal("118.00"), Decimal("113.00"), Decimal("117.50"), Decimal("113.00"), Decimal("170.00"), Decimal("122.00"), Decimal("119.00"), Decimal("117.00")],
    18: [Decimal("132.00"), Decimal("115.00"), Decimal("121.50"), Decimal("117.50"), Decimal("121.00"), Decimal("117.50"), Decimal("175.00"), Decimal("126.00"), Decimal("123.00"), Decimal("121.00")],
    19: [Decimal("136.50"), Decimal("118.00"), Decimal("125.00"), Decimal("122.00"), Decimal("124.50"), Decimal("122.00"), Decimal("180.00"), Decimal("130.00"), Decimal("127.00"), Decimal("125.00")],
    20: [Decimal("141.00"), Decimal("121.00"), Decimal("128.50"), Decimal("126.50"), Decimal("128.00"), Decimal("126.50"), Decimal("185.00"), Decimal("134.00"), Decimal("131.00"), Decimal("129.00")],
}


class Command(BaseCommand):
    help = "Kargo firmalarını ve varsayılan desi fiyat tablosunu oluşturur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Mevcut global varsayılan fiyatları sil ve yeniden oluştur.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        # 1. Kargo firmalarını oluştur
        company_objs = {}
        for c in COMPANIES:
            obj, created = CargoCompany.objects.get_or_create(
                code=c["code"],
                defaults={"name": c["name"], "is_active": True},
            )
            if not created and obj.name != c["name"]:
                obj.name = c["name"]
                obj.save(update_fields=["name"])
            company_objs[c["code"]] = obj
            status = "oluşturuldu" if created else "mevcut"
            self.stdout.write(f"  {c['name']} ({c['code']}) — {status}")

        self.stdout.write(self.style.SUCCESS(f"\n✓ {len(company_objs)} kargo firması hazır."))

        # 2. Global varsayılan fiyatları oluştur (organization=None)
        if reset:
            deleted_count, _ = CargoRate.objects.filter(organization__isnull=True).delete()
            self.stdout.write(f"  {deleted_count} eski global fiyat silindi.")

        codes_ordered = [c["code"] for c in COMPANIES]
        created_count = 0
        updated_count = 0

        for desi, prices in DEFAULT_RATES.items():
            for idx, code in enumerate(codes_ordered):
                company = company_objs[code]
                price = prices[idx]
                obj, created = CargoRate.objects.update_or_create(
                    organization=None,
                    cargo_company=company,
                    desi_kg=desi,
                    defaults={"price": price, "is_active": True},
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✓ Global fiyat tablosu: {created_count} yeni, {updated_count} güncellendi."
        ))
        self.stdout.write(self.style.SUCCESS("\n🚚 Kargo seed tamamlandı!"))
