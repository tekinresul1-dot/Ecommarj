from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0030_cargoinvoice_parcel_unique_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="fast_delivery",
            field=models.BooleanField(default=False, verbose_name="Hızlı Teslimat / Bugün Kargoda"),
        ),
    ]
