from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0026_seed_subscription_plans_and_users"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "order_number"],
                name="ord_org_ordernum_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "marketplace_order_id"],
                name="ord_org_mktid_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(
                fields=["order", "product_variant"],
                name="oi_order_variant_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(fields=["sku"], name="oi_sku_idx"),
        ),
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(
                fields=["organization", "transaction_type"],
                name="ft_org_type_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(
                fields=["order_item_ref", "transaction_type"],
                name="ft_itemref_type_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(
                fields=["organization", "created_at"],
                name="ft_org_created_idx",
            ),
        ),
    ]
