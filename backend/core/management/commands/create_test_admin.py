"""
Yönetici paneli için test verisi oluşturur.

Çalıştırma (Docker):
    docker compose exec backend python manage.py create_test_admin

Oluşturulanlar:
  * Superuser  — admin@ecommarj.com / Admin123!
  * 5 test kullanıcısı (aktif / aktif / trial / pasif / askıya alınmış)
  * Her birine örnek abonelik + ödeme kaydı
  * 1 örnek giriş kodu

Idempotent — varsa günceller, eksik olanı oluşturur.
"""
import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Yönetici paneli için superuser + test kullanıcıları oluşturur."

    ADMIN_EMAIL = "admin@ecommarj.com"
    ADMIN_PASS = "Admin123!"

    TEST_USERS = [
        # email, full_name, status, sub_status, plan_type, payment_status
        ("test.active1@ecommarj.com", "Aktif Kullanıcı 1", "active",   "active",  "monthly", "paid"),
        ("test.active2@ecommarj.com", "Aktif Kullanıcı 2", "active",   "active",  "yearly",  "paid"),
        ("test.trial@ecommarj.com",   "Trial Kullanıcı",   "trial",    "trial",   "free_trial", "pending"),
        ("test.passive@ecommarj.com", "Pasif Kullanıcı",   "passive",  "expired", "monthly", "overdue"),
        ("test.suspended@ecommarj.com","Askıya Alınmış",   "suspended","cancelled","monthly", "refunded"),
    ]

    def handle(self, *args, **options):
        from core.models import (
            UserProfile, Organization, SubscriptionPlan, UserSubscription,
            Payment, AccessCode,
        )
        from core.services.access_code_service import generate_code

        # 1) Superuser
        admin, created = User.objects.get_or_create(
            username=self.ADMIN_EMAIL,
            defaults={"email": self.ADMIN_EMAIL, "first_name": "Admin", "last_name": "EcomMarj"},
        )
        admin.email = self.ADMIN_EMAIL
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.set_password(self.ADMIN_PASS)
        admin.save()
        self.stdout.write(self.style.SUCCESS(
            f"{'✓ Superuser oluşturuldu' if created else '✓ Superuser güncellendi'}: {self.ADMIN_EMAIL}"
        ))

        # 2) Planlar (yoksa oluştur — mevcut seed migration'ı varsa pas geç)
        plan_specs = [
            ("Starter Aylık",  "monthly",    Decimal("199.00"),  30,  "starter"),
            ("Business Yıllık","yearly",     Decimal("1990.00"), 365, "business"),
            ("Free Trial",     "free_trial", Decimal("0.00"),    14,  "starter"),
        ]
        plans_by_type = {}
        for name, ptype, price, days, tier in plan_specs:
            plan, _ = SubscriptionPlan.objects.get_or_create(
                name=name,
                defaults={
                    "price": price, "interval": "yearly" if ptype == "yearly" else "monthly",
                    "plan_type": ptype, "plan_tier": tier, "duration_days": days,
                    "order_limit": 5000 if tier == "business" else 1000,
                    "store_limit": 5 if tier == "business" else 1,
                    "is_active": True,
                },
            )
            # Mevcut ise plan_type/duration alanlarını da güncelle
            updated = False
            if not plan.plan_type:
                plan.plan_type = ptype
                updated = True
            if plan.duration_days is None:
                plan.duration_days = days
                updated = True
            if updated:
                plan.save(update_fields=["plan_type", "duration_days"])
            plans_by_type[ptype] = plan

        # 3) Test kullanıcıları
        now = timezone.now()
        for email, full_name, user_status, sub_status, plan_type, pay_status in self.TEST_USERS:
            first, _, last = full_name.partition(" ")
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": first, "last_name": last},
            )
            user.email = email
            user.set_password("Test123!")
            user.is_active = user_status != "passive"
            user.save()

            org, _ = Organization.objects.get_or_create(name=f"{full_name} Firması")
            profile, _ = UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "organization": org,
                    "company": f"{full_name} Firması",
                    "phone": "+90 555 000 0000",
                    "is_suspended": user_status == "suspended",
                    "suspension_reason": "Test verisi — askıya alınmış kullanıcı" if user_status == "suspended" else "",
                    "is_priority": user_status == "active" and email.endswith("active1@ecommarj.com"),
                    "is_risky": user_status == "passive",
                    "email_verified": user_status != "trial",
                },
            )

            plan = plans_by_type.get(plan_type) or plans_by_type["monthly"]
            # Abonelik
            duration = plan.duration_days or 30
            start = now - timedelta(days=10) if sub_status not in ("trial",) else now
            end = start + timedelta(days=duration)
            if sub_status == "expired":
                end = now - timedelta(days=5)
            elif sub_status == "cancelled":
                end = start + timedelta(days=5)
            UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    "plan": plan, "status": sub_status,
                    "start_date": start, "end_date": end,
                    "current_period_end": end,
                    "trial_end_date": end if sub_status == "trial" else None,
                    "created_by_admin": admin,
                    "notes": "Otomatik oluşturulan test verisi",
                },
            )

            # Ödeme
            Payment.objects.update_or_create(
                merchant_oid=f"TEST_{email}",
                defaults={
                    "user": user, "plan": plan, "amount": plan.price,
                    "status": pay_status,
                    "payment_date": now - timedelta(days=2) if pay_status == "paid" else None,
                    "due_date": now - timedelta(days=10) if pay_status == "overdue" else None,
                    "invoice_note": "Test kaydı",
                    "added_by_admin": True,
                },
            )

            self.stdout.write(self.style.SUCCESS(
                f"  ✓ {'oluşturuldu' if created else 'güncellendi'}: {email}  ({user_status}/{sub_status}/{pay_status})"
            ))

        # 4) Aktif kullanıcıdan birine örnek erişim kodu
        try:
            sample_user = User.objects.get(email="test.active1@ecommarj.com")
            if not AccessCode.objects.filter(user=sample_user, is_active=True).exists():
                ac = generate_code(sample_user, admin=admin, is_lifetime=True)
                self.stdout.write(self.style.SUCCESS(f"  ✓ örnek erişim kodu: {ac.code}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ! erişim kodu oluşturulamadı: {e}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Tamamlandı. Yönetici girişi: {self.ADMIN_EMAIL} / {self.ADMIN_PASS}"
        ))
        self.stdout.write(self.style.WARNING(
            "Üretimde test kullanıcılarını ve admin parolasını DEĞİŞTİRİN."
        ))
