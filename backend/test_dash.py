import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()

client = Client()
client.force_login(user)
response = client.get('/api/dashboard/overview/')
print(response.status_code)
try:
    print(response.json())
except:
    print(response.content)
