import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecompro_backend.settings')
django.setup()

from core.models import CargoPricing

# Sadece ihtiyacımız olan, en sık kullanılan kargoları alıyoruz (Sütunlar: 0:Desi, 1:Aras, 4:PTT, 5:Sürat, 6:TEX, 7:Yurtiçi)
# Raw text contains output like:
# 1 49,38 72,00 52,00 48,00 49,38 49,38 49,38 49,38 49,38 49,38
# 2 54,42 75,00 55,50 50,00 54,42 54,42 54,42 54,42 54,42 54,42

raw_data = """
1 49,38 72,00 52,00 48,00 49,38 49,38 49,38 49,38 49,38 49,38
2 54,42 75,00 55,50 50,00 54,42 54,42 54,42 54,42 54,42 54,42
3 58,16 78,00 59,50 52,00 58,16 58,16 58,16 58,16 58,16 58,16
4 61,84 81,00 63,50 54,00 61,84 61,84 61,84 61,84 61,84 61,84
5 65,37 84,00 66,50 55,00 65,37 65,37 65,37 65,37 65,37 65,37
6 71,60 92,00 72,00 60,00 71,60 71,60 71,60 71,60 71,60 71,60
7 77,26 99,00 78,00 64,00 77,26 77,26 77,26 77,26 77,26 77,26
8 83,57 107,00 84,00 69,00 83,57 83,57 83,57 83,57 83,57 83,57
9 89,88 115,00 90,00 74,00 89,88 89,88 89,88 89,88 89,88 89,88
10 96,18 123,00 95,50 78,00 96,18 96,18 96,18 96,18 96,18 96,18
11 106,89 137,00 106,00 88,00 106,89 106,89 106,89 106,89 106,89 106,89
12 117,60 151,00 116,50 97,00 117,60 117,60 117,60 117,60 117,60 117,60
13 128,30 165,00 127,00 105,00 128,30 128,30 128,30 128,30 128,30 128,30
14 139,01 179,00 137,50 114,00 139,01 139,01 139,01 139,01 139,01 139,01
15 149,72 193,00 148,00 122,00 149,72 149,72 149,72 149,72 149,72 149,72
16 160,42 207,00 158,50 131,00 160,42 160,42 160,42 160,42 160,42 160,42
17 171,13 221,00 169,00 139,00 171,13 171,13 171,13 171,13 171,13 171,13
18 181,84 235,00 179,50 148,00 181,84 181,84 181,84 181,84 181,84 181,84
19 192,54 249,00 190,00 156,00 192,54 192,54 192,54 192,54 192,54 192,54
20 203,25 263,00 200,50 165,00 203,25 203,25 203,25 203,25 203,25 203,25
21 213,96 277,00 211,00 174,00 213,96 213,96 213,96 213,96 213,96 213,96
22 224,66 291,00 221,50 182,00 224,66 224,66 224,66 224,66 224,66 224,66
23 235,37 305,00 232,00 191,00 235,37 235,37 235,37 235,37 235,37 235,37
24 246,08 319,00 242,50 199,00 246,08 246,08 246,08 246,08 246,08 246,08
25 256,78 333,00 253,00 208,00 256,78 256,78 256,78 256,78 256,78 256,78
26 267,49 347,00 263,50 216,00 267,49 267,49 267,49 267,49 267,49 267,49
27 278,20 361,00 274,00 225,00 278,20 278,20 278,20 278,20 278,20 278,20
28 288,90 375,00 284,50 233,00 288,90 288,90 288,90 288,90 288,90 288,90
29 299,61 389,00 295,00 242,00 299,61 299,61 299,61 299,61 299,61 299,61
30 310,32 403,00 305,50 251,00 310,32 310,32 310,32 310,32 310,32 310,32
"""

def run():
    print("Seeding Cargo Prices...")
    CargoPricing.objects.all().delete()
    
    lines = raw_data.strip().split('\n')
    
    count = 0
    for line in lines:
        parts = line.strip().split()
        if not parts or not parts[0].isdigit():
            continue
            
        desi = Decimal(parts[0])
        
        # Mapping index to carrier name based on PDF headers:
        # Desi/KG(0) Aras(1) DHL(2) Kolay Gelsin(3) PTT(4) Sürat(5) TEX(6) Yurtiçi(7)
        carriers = {
            "Aras Kargo": parts[1],
            "PTT Kargo": parts[4],
            "Sürat Kargo": parts[5],
            "Trendyol Express": parts[6],
            "Yurtiçi Kargo": parts[7]
        }
        
        for name, price_str in carriers.items():
            # Convert 49,38 to 49.38
            price_val = Decimal(price_str.replace(',', '.'))
            
            CargoPricing.objects.create(
                carrier_name=name,
                desi=desi,
                price_without_vat=price_val
            )
            count += 1
            
    print(f"Successfully seeded {count} cargo price rules for 1-30 desi.")
    
    # Generate up to 100 desi algoritmically based on trend
    # From 30 onwards, each desi seems to add around +10.70 TL for TEX/Aras
    last_tex_price = Decimal("310.32")
    last_ptt_price = Decimal("251.00")
    for d in range(31, 101):
        desi_val = Decimal(d)
        
        tex_price = last_tex_price + (desi_val - Decimal(30)) * Decimal("10.70")
        ptt_price = last_ptt_price + (desi_val - Decimal(30)) * Decimal("8.50")
        
        CargoPricing.objects.create(carrier_name="Trendyol Express", desi=desi_val, price_without_vat=tex_price)
        CargoPricing.objects.create(carrier_name="Aras Kargo", desi=desi_val, price_without_vat=tex_price)
        CargoPricing.objects.create(carrier_name="Yurtiçi Kargo", desi=desi_val, price_without_vat=tex_price)
        CargoPricing.objects.create(carrier_name="Sürat Kargo", desi=desi_val, price_without_vat=tex_price)
        CargoPricing.objects.create(carrier_name="PTT Kargo", desi=desi_val, price_without_vat=ptt_price)

    print("Successfully generated extended 31-100 desi rules.")

if __name__ == '__main__':
    run()
