import os
import django
from decimal import Decimal
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import CargoPricing

def run():
    file_path = "/Users/candemir/Desktop/kargofiyatları.xlsx"
    print(f"Reading {file_path}...")
    
    try:
        # The first two rows contain titles/notes, the actual headers are on row index 2
        df = pd.read_excel(file_path, header=2)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # Delete old prices
    CargoPricing.objects.all().delete()
    print("Cleared old CargoPricing rules.")

    desi_col = df.columns[0]
    
    carrier_map = {
        "Aras Kargo": "Aras",
        "PTT Kargo": "PTT",
        "Sürat Kargo": "Sürat",
        "Trendyol Express": "TEX",
        "Yurtiçi Kargo": "Yurtiçi"
    }

    count = 0
    # Iterate through all rows
    for index, row in df.iterrows():
        try:
            # Skip invalid desi rows
            if pd.isna(row[desi_col]):
                continue
                
            desi = Decimal(str(row[desi_col]).strip())
            
            for system_name, excel_col in carrier_map.items():
                if excel_col in df.columns:
                    val = row[excel_col]
                    if not pd.isna(val):
                        # Convert to Decimal, handle any commas or spaces if they bleed in
                        price_str = str(val).replace(',', '.').strip()
                        try:
                            price_val = Decimal(price_str)
                            CargoPricing.objects.create(
                                carrier_name=system_name,
                                desi=desi,
                                price_without_vat=price_val
                            )
                            count += 1
                        except Exception as e:
                            # Safely ignore un-parseable prices (e.g. string headers mid-sheet)
                            pass
        except Exception as e:
            pass # Skip complex errors per row
            
    print(f"Successfully seeded {count} cargo price rules from Excel.")

if __name__ == '__main__':
    run()
