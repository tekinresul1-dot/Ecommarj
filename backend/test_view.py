import os
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommarj_backend.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import force_authenticate
from core.models import Organization, UserProfile
from core.views import DashboardOverviewView

org = Organization.objects.first()
profile = UserProfile.objects.filter(organization=org).first()
if not profile:
    print("No profile for org first!")
    exit(1)

user = profile.user

factory = RequestFactory()
request = factory.get('/api/dashboard/overview?channel=trendyol&min_date=2026-03-01&max_date=2026-03-29')
force_authenticate(request, user=user)

view = DashboardOverviewView.as_view()
response = view(request)

if hasattr(response, 'data'):
    def default_serializer(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    print(json.dumps(response.data.get("kpis"), indent=2, default=default_serializer))
else:
    print("No data in response")
