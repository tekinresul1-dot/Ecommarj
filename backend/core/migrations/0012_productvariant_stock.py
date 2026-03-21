from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_product_trendyol_content_id_variant_color_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='stock',
            field=models.IntegerField(default=0, verbose_name='Stok'),
        ),
    ]
