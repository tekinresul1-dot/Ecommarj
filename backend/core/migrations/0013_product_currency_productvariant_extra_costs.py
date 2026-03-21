from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_productvariant_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='currency',
            field=models.CharField(default='TRY', max_length=10, verbose_name='Para Birimi'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='extra_cost_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='Ekstra Maliyet (%)'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='extra_cost_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Ekstra Maliyet (TL)'),
        ),
    ]
