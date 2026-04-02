from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_returnclaim_updates_returnclaimitem"),
    ]

    operations = [
        migrations.CreateModel(
            name="CheTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("transaction_id", models.CharField(max_length=100, unique=True)),
                ("transaction_date", models.DateTimeField()),
                ("barcode", models.CharField(blank=True, max_length=100, null=True)),
                ("transaction_type", models.CharField(max_length=100)),
                ("source", models.CharField(
                    choices=[("settlements", "Settlements"), ("otherfinancials", "Other Financials")],
                    max_length=50,
                )),
                ("receipt_id", models.BigIntegerField(blank=True, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("debt", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("credit", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("commission_rate", models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ("commission_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("seller_revenue", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("order_number", models.CharField(blank=True, max_length=100, null=True)),
                ("payment_order_id", models.BigIntegerField(blank=True, null=True)),
                ("payment_date", models.DateTimeField(blank=True, null=True)),
                ("organization", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="che_transactions",
                    to="core.organization",
                )),
                ("account", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="che_transactions",
                    to="core.marketplaceaccount",
                )),
            ],
            options={
                "verbose_name": "CHE İşlemi",
                "verbose_name_plural": "CHE İşlemleri",
            },
        ),
        migrations.AddIndex(
            model_name="chetransaction",
            index=models.Index(
                fields=["organization", "transaction_type", "transaction_date"],
                name="core_chetx_org_type_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="chetransaction",
            index=models.Index(
                fields=["order_number"],
                name="core_chetx_order_number_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="chetransaction",
            index=models.Index(
                fields=["barcode"],
                name="core_chetx_barcode_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="chetransaction",
            index=models.Index(
                fields=["organization", "source", "transaction_date"],
                name="core_chetx_org_source_date_idx",
            ),
        ),
    ]
