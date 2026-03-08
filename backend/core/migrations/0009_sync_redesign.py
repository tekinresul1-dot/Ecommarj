"""
Trendyol Sync Redesign Migration
- Add new fields to Order (package_id, order_number, last_modified_date, etc.)
- Populate package_id from marketplace_order_id for existing records
- Add unique_together constraint on (organization, package_id)
- Create SyncCheckpoint, SyncAuditLog, ReturnClaim models
"""
from django.db import migrations, models
import django.db.models.deletion


def populate_package_id(apps, schema_editor):
    """Populate package_id from marketplace_order_id for existing orders."""
    Order = apps.get_model('core', 'Order')
    for order in Order.objects.all():
        if not order.package_id:
            order.package_id = order.marketplace_order_id
            order.order_number = order.marketplace_order_id
            order.save(update_fields=['package_id', 'order_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_order_unique_constraint'),
    ]

    operations = [
        # -- Step 1: Remove old unique_together --
        migrations.AlterUniqueTogether(
            name='order',
            unique_together=set(),
        ),

        # -- Step 2: Add new fields to Order (no constraints yet) --
        migrations.AddField(
            model_name='order',
            name='package_id',
            field=models.CharField(db_index=True, default='', max_length=100, verbose_name='Paket ID (shipmentPackageId)'),
        ),
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(db_index=True, default='', max_length=100, verbose_name='Trendyol Sipariş Numarası'),
        ),
        migrations.AddField(
            model_name='order',
            name='last_modified_date',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Son Değişiklik Tarihi'),
        ),
        migrations.AddField(
            model_name='order',
            name='previous_status',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='Önceki Durum'),
        ),
        migrations.AddField(
            model_name='order',
            name='status_changed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Durum Değişim Tarihi'),
        ),
        migrations.AddField(
            model_name='order',
            name='cargo_provider_name',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Kargo Firması'),
        ),
        migrations.AddField(
            model_name='order',
            name='cargo_tracking_number',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Kargo Takip No'),
        ),
        migrations.AddField(
            model_name='order',
            name='raw_payload_hash',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='Payload Hash'),
        ),
        migrations.AddField(
            model_name='order',
            name='last_synced_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Son Sync Zamanı'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[
                ('Created', 'Oluşturuldu'), ('Picking', 'Hazırlanıyor'),
                ('Shipped', 'Kargoya Verildi'), ('Delivered', 'Teslim Edildi'),
                ('Cancelled', 'İptal'), ('Returned', 'İade'),
                ('UnDelivered', 'Teslim Edilemedi'), ('UnSupplied', 'Tedarik Edilemedi'),
            ], max_length=30),
        ),
        migrations.AlterField(
            model_name='syncjob',
            name='job_type',
            field=models.CharField(choices=[
                ('orders', 'Siparişler'), ('products', 'Ürünler'),
                ('finance', 'Finans / Hakediş'), ('claims', 'İade / Claim'),
                ('reconciliation', 'Reconciliation'),
            ], max_length=30),
        ),

        # -- Step 3: Populate package_id from existing data --
        migrations.RunPython(populate_package_id, migrations.RunPython.noop),

        # -- Step 4: Apply unique_together constraint --
        migrations.AlterUniqueTogether(
            name='order',
            unique_together={('organization', 'package_id')},
        ),

        # -- Step 5: Add indexes --
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['organization', 'order_date'], name='core_order_organiz_da0a54_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['organization', 'last_modified_date'], name='core_order_organiz_c40329_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['organization', 'status'], name='core_order_organiz_f18c7c_idx'),
        ),

        # -- Step 6: Create SyncCheckpoint --
        migrations.CreateModel(
            name='SyncCheckpoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sync_type', models.CharField(choices=[('orders', 'Siparişler'), ('claims', 'İade / Claim'), ('products', 'Ürünler')], max_length=30)),
                ('last_successful_sync_at', models.DateTimeField(verbose_name='Son Başarılı Sync')),
                ('last_fetched_modified_date', models.DateTimeField(blank=True, null=True, verbose_name='Son Çekilen Modified Date')),
                ('marketplace_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_checkpoints', to='core.marketplaceaccount')),
            ],
            options={
                'verbose_name': 'Sync Checkpoint',
                'verbose_name_plural': 'Sync Checkpoints',
                'unique_together': {('marketplace_account', 'sync_type')},
            },
        ),

        # -- Step 7: Create SyncAuditLog --
        migrations.CreateModel(
            name='SyncAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sync_type', models.CharField(max_length=30)),
                ('sync_mode', models.CharField(choices=[('full', 'Full Sync'), ('incremental', 'Incremental Sync'), ('backfill', 'Backfill'), ('reconciliation', 'Reconciliation'), ('webhook', 'Webhook')], max_length=30)),
                ('started_at', models.DateTimeField()),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('date_range_start', models.DateTimeField(blank=True, null=True)),
                ('date_range_end', models.DateTimeField(blank=True, null=True)),
                ('total_fetched', models.IntegerField(default=0)),
                ('inserted', models.IntegerField(default=0)),
                ('updated', models.IntegerField(default=0)),
                ('skipped', models.IntegerField(default=0)),
                ('failed', models.IntegerField(default=0)),
                ('success', models.BooleanField(default=False)),
                ('error_message', models.TextField(blank=True, default='')),
                ('duration_seconds', models.FloatField(default=0)),
                ('marketplace_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_audit_logs', to='core.marketplaceaccount')),
            ],
            options={
                'verbose_name': 'Sync Audit Log',
                'verbose_name_plural': 'Sync Audit Logs',
                'ordering': ['-started_at'],
            },
        ),

        # -- Step 8: Create ReturnClaim --
        migrations.CreateModel(
            name='ReturnClaim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('claim_id', models.CharField(db_index=True, max_length=100, verbose_name='Claim ID')),
                ('order_number', models.CharField(blank=True, default='', max_length=100, verbose_name='Sipariş No')),
                ('claim_date', models.DateTimeField(blank=True, null=True, verbose_name='Claim Tarihi')),
                ('claim_status', models.CharField(choices=[('Created', 'Oluşturuldu'), ('InProgress', 'İşlemde'), ('Resolved', 'Çözümlendi'), ('Rejected', 'Reddedildi')], default='Created', max_length=30)),
                ('reason', models.TextField(blank=True, default='', verbose_name='İade Nedeni')),
                ('refund_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='İade Tutarı')),
                ('cargo_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Kargo Maliyeti')),
                ('raw_payload_hash', models.CharField(blank=True, default='', max_length=64, verbose_name='Payload Hash')),
                ('last_synced_at', models.DateTimeField(blank=True, null=True)),
                ('marketplace_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_claims', to='core.marketplaceaccount')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='claims', to='core.order')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_claims', to='core.organization')),
            ],
            options={
                'verbose_name': 'İade / Claim',
                'verbose_name_plural': 'İade / Claim Kayıtları',
                'unique_together': {('organization', 'claim_id')},
            },
        ),
    ]
