import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

user, created = User.objects.get_or_create(username='test_me_auth@ecommarj.com', email='test_me_auth@ecommarj.com')
user.set_password('testpassword123')
user.save()

tokens = RefreshToken.for_user(user)
access = str(tokens.access_token)

headers = {"Authorization": f"Bearer {access}"}

res = requests.get('http://127.0.0.1:8000/api/auth/me/', headers=headers)
print("GET /api/auth/me/ -> STATUS:", res.status_code)
print(res.text)

res2 = requests.get('http://127.0.0.1:8000/api/dashboard/overview/', headers=headers)
print("GET /api/dashboard/overview/ -> STATUS:", res2.status_code)
print(res2.text[:200])

