import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import MarketplaceAccount
from core.tasks import sync_all_trendyol_data_task

acc = MarketplaceAccount.objects.first()
if acc:
    print("Mevcut Sipariş Sayısı (db.sqlite3):", acc.orders.count())
    sync_all_trendyol_data_task(str(acc.id))
    print("Sync tamamlandı. Yeni Sipariş Sayısı:", acc.orders.count())
else:
    print("Hesap bulunamadı.")
