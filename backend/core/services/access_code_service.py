"""
Yönetici tarafından üretilen, OTP yerine geçen giriş kodları.

Kod biçimi: 8 hanelik alfanumerik büyük harf + rakam (karışıklığı önlemek için
I, O, 0, 1 hariç). Her kullanım `use_count` artar; 5 yanlış denemede ilgili
kullanıcının hesabı (varsa) kilitlenir.
"""

import logging
import secrets
from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

CODE_LENGTH = 8
# I/O/0/1 ve l karıştırılmaz
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MAX_VALIDATION_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _generate_code_string() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def _log(admin, target_user, action_type, description, ip=None, **values):
    try:
        from core.models import AdminLog
        AdminLog.objects.create(
            admin=admin,
            target_user=target_user,
            action_type=action_type,
            description=description,
            new_value=values or None,
            ip_address=ip,
        )
    except Exception as e:
        logger.warning("[AccessCode] AdminLog yazılamadı: %s", e)


@transaction.atomic
def generate_code(user, admin=None, expires_at=None, max_uses=None, is_lifetime=False, ip=None):
    """Benzersiz kod üret. Çakışma olursa 5 kez tekrar dener."""
    from core.models import AccessCode

    for _ in range(5):
        code = _generate_code_string()
        if not AccessCode.objects.filter(code=code).exists():
            obj = AccessCode.objects.create(
                user=user,
                code=code,
                created_by=admin,
                expires_at=None if is_lifetime else expires_at,
                is_active=True,
                is_lifetime=is_lifetime,
                max_uses=max_uses,
            )
            _log(
                admin, user, "code_create",
                f"{user.email} için giriş kodu oluşturuldu (lifetime={is_lifetime}).",
                ip=ip,
                expires_at=expires_at.isoformat() if expires_at else None,
                max_uses=max_uses,
            )
            return obj
    raise RuntimeError("Benzersiz kod üretilemedi — lütfen tekrar deneyin.")


def validate_code(code: str, ip: str = "") -> "tuple[object | None, str]":
    """Kod geçerli mi? (access_code, error_message). Hatalı denemeler cache'te
    sayılır; MAX_VALIDATION_ATTEMPTS aşılırsa LOCKOUT_MINUTES boyunca tüm kod
    denemeleri (bu IP için) reddedilir."""
    from core.models import AccessCode

    if not code:
        return None, "Kod gereklidir."

    code = code.strip().upper()
    lockout_key = f"access_code_lockout_{ip or 'noip'}"
    attempt_key = f"access_code_attempts_{ip or 'noip'}"

    if cache.get(lockout_key):
        return None, "Çok fazla hatalı kod denemesi. Lütfen 15 dakika sonra tekrar deneyin."

    ac = AccessCode.objects.select_related("user").filter(code=code).first()
    if not ac or not ac.is_usable():
        attempts = cache.get(attempt_key, 0) + 1
        cache.set(attempt_key, attempts, timeout=LOCKOUT_MINUTES * 60)
        if attempts >= MAX_VALIDATION_ATTEMPTS:
            cache.set(lockout_key, True, timeout=LOCKOUT_MINUTES * 60)
            cache.delete(attempt_key)
            return None, "Çok fazla hatalı kod denemesi. 15 dakika sonra tekrar deneyin."
        return None, "Kod geçersiz veya süresi dolmuş."

    # Başarılı doğrulama → sayaçları sıfırla, kullanım istatistiklerini güncelle
    cache.delete(attempt_key)
    ac.use_count = (ac.use_count or 0) + 1
    ac.last_used_at = timezone.now()
    ac.save(update_fields=["use_count", "last_used_at"])
    return ac, ""


def deactivate_code(access_code, admin=None, ip=None):
    """Kodu pasife alır."""
    access_code.is_active = False
    access_code.save(update_fields=["is_active"])
    _log(
        admin, access_code.user, "code_delete",
        f"Giriş kodu pasife alındı ({access_code.code[:2]}***).",
        ip=ip,
    )
    return access_code


def regenerate_code(access_code, admin=None, ip=None):
    """Mevcut kaydı pasife alıp yeni bir kod üretir (aynı politikalarla)."""
    deactivate_code(access_code, admin=admin, ip=ip)
    new_obj = generate_code(
        access_code.user,
        admin=admin,
        expires_at=access_code.expires_at,
        max_uses=access_code.max_uses,
        is_lifetime=access_code.is_lifetime,
        ip=ip,
    )
    _log(admin, access_code.user, "code_regenerate", "Giriş kodu yeniden üretildi.", ip=ip)
    return new_obj
