from django.db import migrations, models


INITIAL_RATES = [
    ("Yurtiçi Kargo",    "135.32", "Trendyol tarife Mar 2026"),
    ("Aras Kargo",       "96.00",  ""),
    ("Sürat Kargo",      "103.00", ""),
    ("Trendyol Express", "87.50",  ""),
    ("PTT Kargo",        "87.50",  ""),
    ("MNG Kargo",        "96.00",  ""),
    ("Kolay Gelsin",     "105.50", ""),
    ("Hepsijet",         "90.00",  ""),
    ("DHL eCommerce",    "107.00", ""),
    ("Kargoist",         "90.00",  ""),
    ("Kargom",           "90.00",  ""),
]


def populate_rates(apps, schema_editor):
    CarrierFlatRate = apps.get_model("core", "CarrierFlatRate")
    for carrier, rate, notes in INITIAL_RATES:
        CarrierFlatRate.objects.get_or_create(
            carrier_name=carrier,
            defaults={"rate_kdv_dahil": rate, "notes": notes},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_order_cargo_deci_cargo_cost"),
    ]

    operations = [
        migrations.CreateModel(
            name="CarrierFlatRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("carrier_name", models.CharField(max_length=100, unique=True, verbose_name="Kargo Firması")),
                ("rate_kdv_dahil", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Flat Rate (KDV Dahil, TL)")),
                ("notes", models.CharField(blank=True, default="", max_length=255, verbose_name="Not")),
            ],
            options={
                "verbose_name": "Kargo Flat Tarife",
                "verbose_name_plural": "Kargo Flat Tarifeleri",
                "ordering": ["carrier_name"],
            },
        ),
        migrations.RunPython(populate_rates, migrations.RunPython.noop),
    ]
