import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()
from core.models import MarketplaceAccount, UserProfile
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='mahfelce@gmail.com')
account = MarketplaceAccount.objects.get(organization=user.profile.organization, is_active=True)
print(f'API KEY in DB: {account.api_key}')
