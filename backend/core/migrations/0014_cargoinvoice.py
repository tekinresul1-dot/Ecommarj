from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_product_currency_productvariant_extra_costs'),
    ]

    operations = [
        migrations.CreateModel(
            name='CargoInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_number', models.CharField(db_index=True, max_length=50, verbose_name='Sipariş No')),
                ('invoice_serial_number', models.CharField(max_length=100, verbose_name='Fatura Seri No')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Kargo Tutarı (KDV Dahil)')),
                ('desi', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Desi')),
                ('shipment_package_type', models.CharField(blank=True, max_length=200, verbose_name='Gönderi Tipi')),
                ('raw_payload', models.JSONField(blank=True, default=dict, verbose_name='Ham Veri')),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cargo_invoices',
                    to='core.organization',
                )),
            ],
            options={
                'verbose_name': 'Kargo Faturası Kalemi',
                'verbose_name_plural': 'Kargo Faturası Kalemleri',
            },
        ),
        migrations.AddIndex(
            model_name='cargoinvoice',
            index=models.Index(fields=['organization', 'order_number'], name='core_cargoi_organiz_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='cargoinvoice',
            unique_together={('organization', 'order_number', 'invoice_serial_number')},
        ),
    ]
