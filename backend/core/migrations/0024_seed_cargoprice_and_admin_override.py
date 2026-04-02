"""
Data migration:
1. CargoPrice tablosunu 0-30 desi için ₺135.32 ile doldur
2. Mevcut tüm kullanıcılara admin_override=True abonelik oluştur (erişim kaybetmesinler)
"""
from django.db import migrations
from decimal import Decimal


def seed_cargo_prices(apps, schema_editor):
    CargoPrice = apps.get_model("core", "CargoPrice")
    for i in range(31):
        CargoPrice.objects.get_or_create(
            desi=i,
            defaults={"price": Decimal("135.32"), "cargo_provider": "Yurtiçi Kargo", "is_active": True},
        )


def seed_admin_override_subscriptions(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserSubscription = apps.get_model("core", "UserSubscription")
    for user in User.objects.all():
        UserSubscription.objects.get_or_create(
            user=user,
            defaults={"status": "admin_override", "admin_override": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_add_cargoprice_subscriptionplan_usersubscription"),
    ]

    operations = [
        migrations.RunPython(seed_cargo_prices, migrations.RunPython.noop),
        migrations.RunPython(seed_admin_override_subscriptions, migrations.RunPython.noop),
    ]
