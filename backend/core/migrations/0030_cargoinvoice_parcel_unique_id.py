from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0029_expand_chetransaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="cargoinvoice",
            name="parcel_unique_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=100, verbose_name="Paket / Koli ID"),
        ),
        migrations.AlterUniqueTogether(
            name="cargoinvoice",
            unique_together={("organization", "order_number", "invoice_serial_number", "parcel_unique_id")},
        ),
    ]
