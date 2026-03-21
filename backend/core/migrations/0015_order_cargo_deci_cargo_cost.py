from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_cargoinvoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cargo_deci',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=8,
                null=True, verbose_name="Kargo Desi (Trendyol'dan)"
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='cargo_cost',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10,
                null=True, verbose_name='Kargo Maliyeti (Hesaplanan)'
            ),
        ),
    ]
