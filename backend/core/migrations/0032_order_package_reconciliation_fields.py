from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031_order_fast_delivery"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Paket Oluşum Tipi"),
        ),
        migrations.AddField(
            model_name="order",
            name="package_gross_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Paket Brüt Tutar"),
        ),
        migrations.AddField(
            model_name="order",
            name="package_seller_discount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Paket Satıcı İndirimi"),
        ),
        migrations.AddField(
            model_name="order",
            name="package_ty_discount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Paket Trendyol İndirimi"),
        ),
        migrations.AddField(
            model_name="order",
            name="package_total_discount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Paket Toplam İndirim"),
        ),
        migrations.AddField(
            model_name="order",
            name="raw_payload",
            field=models.JSONField(blank=True, default=dict, verbose_name="Ham Trendyol Paket Verisi"),
        ),
    ]
