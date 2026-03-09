import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import traceback

User = get_user_model()
user = User.objects.first()

token = str(RefreshToken.for_user(user).access_token)
client = Client()

try:
    response = client.get('/api/dashboard/overview/', HTTP_HOST='localhost:8000', HTTP_AUTHORIZATION=f'Bearer {token}')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        print("Response Content:")
        print(response.content.decode('utf-8'))
    else:
        print("Success! Response:")
        print(response.content.decode('utf-8')[:300])
except Exception as e:
    traceback.print_exc()
