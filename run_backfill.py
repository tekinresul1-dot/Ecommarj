import os
import django
from datetime import datetime
from zoneinfo import ZoneInfo
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()
from core.models import MarketplaceAccount, UserProfile
from core.services.order_sync import TrendyolOrderSyncService
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='mahfelce@gmail.com')
account = MarketplaceAccount.objects.get(organization=user.profile.organization, is_active=True)
tz = ZoneInfo('Europe/Istanbul')
start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=tz)
end = datetime(2026, 4, 30, 23, 59, 59, tzinfo=tz)
print(f'Backfilling for {account.seller_id} from {start} to {end}...')
svc = TrendyolOrderSyncService(account)
audit = svc.backfill_sync(start_date=start, end_date=end)
print(f'Backfill complete. Fetched: {audit.total_fetched}, Inserted: {audit.inserted}, Updated: {audit.updated}, Failed: {audit.failed}')
