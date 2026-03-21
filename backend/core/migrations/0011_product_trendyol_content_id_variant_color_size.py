from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_userprofile_onboarding_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='trendyol_content_id',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Trendyol İçerik ID'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='color',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Renk'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='size',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Beden'),
        ),
    ]
