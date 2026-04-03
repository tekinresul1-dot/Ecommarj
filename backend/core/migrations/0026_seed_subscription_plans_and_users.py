"""
Data migration:
1. Abonelik planlarını ekle (Starter/Business/Enterprise, aylık/yıllık)
2. Mevcut kullanıcılara admin_override=True abonelik oluştur
"""
from django.db import migrations
from decimal import Decimal


def seed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("core", "SubscriptionPlan")
    plans = [
        dict(name="Starter Aylık",    price=Decimal("499"),  interval="monthly", plan_tier="starter",    order_limit=1000,  store_limit=1, yearly_total=None),
        dict(name="Starter Yıllık",   price=Decimal("399"),  interval="yearly",  plan_tier="starter",    order_limit=1000,  store_limit=1, yearly_total=Decimal("4788")),
        dict(name="Business Aylık",   price=Decimal("899"),  interval="monthly", plan_tier="business",   order_limit=5000,  store_limit=2, yearly_total=None),
        dict(name="Business Yıllık",  price=Decimal("699"),  interval="yearly",  plan_tier="business",   order_limit=5000,  store_limit=2, yearly_total=Decimal("8388")),
        dict(name="Enterprise Aylık", price=Decimal("1999"), interval="monthly", plan_tier="enterprise", order_limit=30000, store_limit=5, yearly_total=None),
        dict(name="Enterprise Yıllık",price=Decimal("1599"), interval="yearly",  plan_tier="enterprise", order_limit=30000, store_limit=5, yearly_total=Decimal("19188")),
    ]
    for p in plans:
        SubscriptionPlan.objects.get_or_create(name=p["name"], defaults=p)


def seed_user_overrides(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserSubscription = apps.get_model("core", "UserSubscription")
    for user in User.objects.all():
        obj, created = UserSubscription.objects.get_or_create(user=user)
        if not obj.admin_override:
            obj.status = "admin_override"
            obj.admin_override = True
            obj.admin_override_reason = "Mevcut kullanıcı - otomatik aktif"
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0025_add_payment_model_update_subscriptionplan"),
    ]

    operations = [
        migrations.RunPython(seed_plans, migrations.RunPython.noop),
        migrations.RunPython(seed_user_overrides, migrations.RunPython.noop),
    ]
