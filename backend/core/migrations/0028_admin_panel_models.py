"""
Yönetici paneli için model genişletmeleri + yeni modeller.

Mevcut UserProfile/SubscriptionPlan/UserSubscription/Payment alanlarına eklemeler
yapılıyor; eski alanlar/değerler korunuyor. Status choice değişiklikleri yalnızca
validation seviyesinde olduğundan ayrı bir AlterField ile gelecekte
`makemigrations` çalıştırıldığında yakalanabilir (zararsız).
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0027_add_performance_indexes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- UserProfile genişletmeleri ---
        migrations.AddField(
            model_name="userprofile",
            name="is_suspended",
            field=models.BooleanField(default=False, verbose_name="Askıya Alındı"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="suspension_reason",
            field=models.TextField(blank=True, default="", verbose_name="Askıya Alma Nedeni"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="admin_note",
            field=models.TextField(blank=True, default="", verbose_name="Admin Notu"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="is_priority",
            field=models.BooleanField(default=False, verbose_name="Öncelikli"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="is_risky",
            field=models.BooleanField(default=False, verbose_name="Riskli"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="admin_override",
            field=models.BooleanField(default=False, verbose_name="Admin Override (Erişim)"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="last_login_ip",
            field=models.GenericIPAddressField(blank=True, null=True, verbose_name="Son Giriş IP"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="email_verified",
            field=models.BooleanField(default=False, verbose_name="E-posta Doğrulandı"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="google_connected",
            field=models.BooleanField(default=False, verbose_name="Google Bağlı"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="trendyol_store_count",
            field=models.IntegerField(default=0, verbose_name="Trendyol Mağaza Sayısı"),
        ),

        # --- SubscriptionPlan genişletmeleri ---
        migrations.AddField(
            model_name="subscriptionplan",
            name="plan_type",
            field=models.CharField(
                choices=[
                    ("free_trial", "Free Trial"),
                    ("monthly", "Aylık"),
                    ("yearly", "Yıllık"),
                    ("lifetime", "Ömür Boyu"),
                    ("manual", "Manuel"),
                ],
                default="monthly",
                max_length=20,
                verbose_name="Plan Tipi",
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="duration_days",
            field=models.IntegerField(blank=True, null=True, verbose_name="Süre (gün)"),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="features",
            field=models.JSONField(blank=True, default=dict, verbose_name="Özellikler"),
        ),

        # --- UserSubscription genişletmeleri ---
        migrations.AddField(
            model_name="usersubscription",
            name="start_date",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Başlangıç"),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="end_date",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Bitiş"),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="trial_end_date",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Deneme Bitiş Tarihi"),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="created_by_admin",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_subscriptions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="notes",
            field=models.TextField(blank=True, default="", verbose_name="Notlar"),
        ),

        # --- Payment genişletmeleri ---
        migrations.AddField(
            model_name="payment",
            name="payment_date",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Ödeme Tarihi"),
        ),
        migrations.AddField(
            model_name="payment",
            name="due_date",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Vade Tarihi"),
        ),
        migrations.AddField(
            model_name="payment",
            name="paytr_transaction_id",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="PayTR Transaction ID"),
        ),
        migrations.AddField(
            model_name="payment",
            name="invoice_note",
            field=models.TextField(blank=True, default="", verbose_name="Fatura Notu"),
        ),
        migrations.AddField(
            model_name="payment",
            name="added_by_admin",
            field=models.BooleanField(default=False, verbose_name="Admin Tarafından Eklendi"),
        ),

        # --- Yeni modeller ---
        migrations.CreateModel(
            name="AccessCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32, unique=True, verbose_name="Kod")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True, verbose_name="Son Geçerlilik")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("is_lifetime", models.BooleanField(default=False, verbose_name="Süresiz")),
                ("use_count", models.IntegerField(default=0, verbose_name="Kullanım Sayısı")),
                ("max_uses", models.IntegerField(blank=True, null=True, verbose_name="Maks. Kullanım")),
                ("last_used_at", models.DateTimeField(blank=True, null=True, verbose_name="Son Kullanım")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="issued_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Giriş Kodu",
                "verbose_name_plural": "Giriş Kodları",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="accesscode",
            index=models.Index(fields=["user", "is_active"], name="ac_user_active_idx"),
        ),

        migrations.CreateModel(
            name="LoginAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip_address", models.GenericIPAddressField()),
                ("attempted_at", models.DateTimeField(auto_now_add=True)),
                ("success", models.BooleanField(default=False)),
                ("attempt_type", models.CharField(default="password", max_length=20)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="login_attempts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Giriş Denemesi",
                "verbose_name_plural": "Giriş Denemeleri",
                "ordering": ["-attempted_at"],
            },
        ),
        migrations.AddIndex(
            model_name="loginattempt",
            index=models.Index(fields=["user", "attempted_at"], name="la_user_time_idx"),
        ),
        migrations.AddIndex(
            model_name="loginattempt",
            index=models.Index(fields=["ip_address", "attempted_at"], name="la_ip_time_idx"),
        ),

        migrations.CreateModel(
            name="AccountLockout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("locked_until", models.DateTimeField(verbose_name="Kilit Bitişi")),
                ("reason", models.CharField(max_length=200, verbose_name="Sebep")),
                ("failed_attempts", models.IntegerField(default=0, verbose_name="Başarısız Deneme Sayısı")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lockouts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Hesap Kilidi",
                "verbose_name_plural": "Hesap Kilitleri",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="accountlockout",
            index=models.Index(fields=["user", "locked_until"], name="al_user_until_idx"),
        ),

        migrations.CreateModel(
            name="AdminLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("user_activate", "Kullanıcı Aktifleştirme"),
                            ("user_deactivate", "Kullanıcı Pasifleştirme"),
                            ("user_suspend", "Kullanıcı Askıya Alma"),
                            ("user_unsuspend", "Askıdan Çıkarma"),
                            ("user_update", "Kullanıcı Güncelleme"),
                            ("plan_change", "Plan Değişikliği"),
                            ("subscription_create", "Abonelik Oluşturma"),
                            ("subscription_extend", "Abonelik Uzatma"),
                            ("subscription_cancel", "Abonelik İptal"),
                            ("subscription_trial", "Trial Başlat/Uzat"),
                            ("code_create", "Kod Oluşturma"),
                            ("code_delete", "Kod Silme"),
                            ("code_regenerate", "Kod Yenileme"),
                            ("payment_add", "Ödeme Ekleme"),
                            ("payment_edit", "Ödeme Düzenleme"),
                            ("override_set", "Manuel Override"),
                            ("note_add", "Not Ekleme"),
                        ],
                        max_length=40,
                    ),
                ),
                ("description", models.TextField()),
                ("old_value", models.JSONField(blank=True, null=True)),
                ("new_value", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                (
                    "admin",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="admin_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "target_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="received_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Admin Logu",
                "verbose_name_plural": "Admin Logları",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="adminlog",
            index=models.Index(fields=["admin", "created_at"], name="al_admin_time_idx"),
        ),
        migrations.AddIndex(
            model_name="adminlog",
            index=models.Index(fields=["target_user", "created_at"], name="al_target_time_idx"),
        ),
        migrations.AddIndex(
            model_name="adminlog",
            index=models.Index(fields=["action_type", "created_at"], name="al_action_time_idx"),
        ),
    ]
