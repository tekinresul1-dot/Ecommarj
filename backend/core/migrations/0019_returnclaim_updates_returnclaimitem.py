from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_add_ad_expense_model"),
    ]

    operations = [
        # Add new fields to ReturnClaim
        migrations.AddField(
            model_name="returnclaim",
            name="order_date",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Sipariş Tarihi"),
        ),
        migrations.AddField(
            model_name="returnclaim",
            name="last_modified_date",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Son Güncelleme"),
        ),
        migrations.AddField(
            model_name="returnclaim",
            name="cargo_provider",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Kargo Firması"),
        ),
        # Update ClaimStatus choices (just alter field to support new max_length if needed)
        migrations.AlterField(
            model_name="returnclaim",
            name="claim_status",
            field=models.CharField(
                choices=[
                    ("Created", "Oluşturuldu"),
                    ("InProgress", "İşlemde"),
                    ("Resolved", "Çözümlendi"),
                    ("Rejected", "Reddedildi"),
                    ("Accepted", "Onaylandı"),
                    ("WaitingInAction", "Aksiyon Bekliyor"),
                    ("Unresolved", "Çözümsüz"),
                ],
                default="Created",
                max_length=30,
            ),
        ),
        # Create ReturnClaimItem
        migrations.CreateModel(
            name="ReturnClaimItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product_name", models.CharField(blank=True, default="", max_length=500, verbose_name="Ürün Adı")),
                ("barcode", models.CharField(blank=True, default="", max_length=100, verbose_name="Barkod")),
                ("merchant_sku", models.CharField(blank=True, default="", max_length=100, verbose_name="Satıcı SKU")),
                ("price", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Birim Fiyat")),
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="Adet")),
                ("claim_item_status", models.CharField(blank=True, default="", max_length=50, verbose_name="Kalem Durumu")),
                ("customer_reason", models.CharField(blank=True, default="", max_length=500, verbose_name="Müşteri İade Nedeni")),
                ("outgoing_cargo_cost", models.DecimalField(decimal_places=2, default=135.32, max_digits=10, verbose_name="Giden Kargo")),
                ("incoming_cargo_cost", models.DecimalField(decimal_places=2, default=135.32, max_digits=10, verbose_name="Gelen Kargo")),
                (
                    "claim",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="claim_items",
                        to="core.returnclaim",
                    ),
                ),
            ],
            options={
                "verbose_name": "İade Kalem",
                "verbose_name_plural": "İade Kalemleri",
            },
        ),
    ]
