import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from core.models import Order, Organization, UserProfile
from core.views import OrderListView
from rest_framework.test import APIRequestFactory, force_authenticate

factory = APIRequestFactory()
user_profile = UserProfile.objects.filter(organization_id=4).first()
if not user_profile:
    print("User for Org 4 not found")
    exit()

# NO DATE FILTERS
request = factory.get('/api/orders/')
force_authenticate(request, user=user_profile.user)
view = OrderListView.as_view()
response = view(request)

if response.status_code == 200:
    results = response.data.get('data', [])
    print(f"Found {len(results)} orders in Org 4")
    for o in results[:10]:
        print(f"ID: {o['id']}, OrderNumber (Display): {o['order_number']}, Date: {o.get('order_date')}")
else:
    print(f"Error: {response.status_code}")
