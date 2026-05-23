from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_admin_panel_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chetransaction",
            name="transaction_id",
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="transaction_type_code",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="transaction_sub_type",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="chetransaction",
            name="commission_amount",
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True),
        ),
        migrations.AlterField(
            model_name="chetransaction",
            name="seller_revenue",
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="shipment_package_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="payment_period",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="commission_invoice_serial_number",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="seller_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="store_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="store_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="store_address",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="country",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="affiliate",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="order_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chetransaction",
            name="raw_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddIndex(
            model_name="chetransaction",
            index=models.Index(fields=["account", "source", "transaction_id"], name="core_chetra_account_3f3e5a_idx"),
        ),
        migrations.AddIndex(
            model_name="chetransaction",
            index=models.Index(fields=["payment_order_id"], name="core_chetra_payment_64cc5c_idx"),
        ),
        migrations.AddConstraint(
            model_name="chetransaction",
            constraint=models.UniqueConstraint(
                fields=("account", "source", "transaction_id"),
                name="core_chetx_account_source_txid_uniq",
            ),
        ),
    ]
