from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0032_order_package_reconciliation_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("Awaiting", "Ödeme Bekliyor"),
                    ("Created", "Oluşturuldu"),
                    ("Picking", "Hazırlanıyor"),
                    ("Invoiced", "Faturalandı"),
                    ("Shipped", "Kargoya Verildi"),
                    ("AtCollectionPoint", "Teslimat Noktasında"),
                    ("Delivered", "Teslim Edildi"),
                    ("Cancelled", "İptal"),
                    ("Returned", "İade"),
                    ("UnDelivered", "Teslim Edilemedi"),
                    ("UnSupplied", "Tedarik Edilemedi"),
                    ("UnPacked", "Paket Bölündü"),
                    ("Repack", "Tekrar Paketlendi"),
                ],
                max_length=30,
            ),
        ),
    ]
