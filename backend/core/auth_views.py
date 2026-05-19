"""
Auth views for EcomMarj — register, login, me.
"""

import logging
import secrets

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from core.models import Organization, UserProfile
from core.throttles import LoginRateThrottle, OTPRateThrottle
from .auth_serializers import RegisterSerializer, LoginSerializer, GoogleLoginSerializer, UserSerializer


logger = logging.getLogger(__name__)


def _get_tokens_for_user(user):
    """Generate JWT token pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _build_company_name(first_name: str, last_name: str) -> str:
    full_name = f"{first_name} {last_name}".strip()
    return full_name or "EcomMarj Kullanıcısı"


def _ensure_user_profile(user: User, *, company_name: str = "", phone: str = "") -> None:
    profile = getattr(user, "profile", None)
    resolved_company = company_name.strip() or _build_company_name(user.first_name, user.last_name)

    if profile and profile.organization:
        organization = profile.organization
        if company_name.strip():
            organization.name = resolved_company
            organization.save(update_fields=["name"])
    else:
        organization = Organization.objects.create(name=resolved_company)

    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            "organization": organization,
            "phone": phone,
            "company": company_name.strip(),
        },
    )


class RegisterView(APIView):
    """POST /api/auth/register/ — yeni hesap oluştur."""

    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            # Check for structured error in the email field
            # DRF may return a list or dict depending on ValidationError detail type
            email_errors = serializer.errors.get("email")
            if email_errors:
                if isinstance(email_errors, list) and email_errors and isinstance(email_errors[0], dict):
                    raw = email_errors[0]
                elif isinstance(email_errors, dict):
                    raw = email_errors
                else:
                    raw = None

                if raw:
                    error_info = raw.get("email", raw) if isinstance(raw, dict) else raw
                    if isinstance(error_info, dict) and error_info.get("code"):
                        return Response(
                            {
                                "error_code": error_info.get("code", "VALIDATION_ERROR"),
                                "message": error_info.get("message", "Doğrulama hatası oluştu."),
                                "next_action": error_info.get("next_action"),
                                "errors": serializer.errors
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            return Response(
                {"error_code": "VALIDATION_ERROR", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        # No token is issued here. The account is inactive until the user
        # proves ownership of the e-mail via the OTP sent below
        # (verified at POST /api/auth/register/verify/).
        email = user.email.lower()
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        try:
            cache.set(f"otp_reg_{email}", otp_code, timeout=600)
            cache.set(f"otp_resend_cooldown_{email}", True, timeout=60)
        except Exception:
            logger.exception("[Register] OTP cache yazılamadı (%s)", email)
            return Response(
                {"error": "Sistem geçici olarak kullanılamıyor. Lütfen tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        subject = "EcomMarj Hesap Doğrulama Kodu"
        message = (
            f"Hesabınızı doğrulamak için kodunuz: {otp_code}\n\n"
            "Bu kod 10 dakika boyunca geçerlidir."
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "info@ecommarj.com")
        try:
            send_mail(subject, message, from_email, [email], fail_silently=False)
        except Exception:
            logger.exception("[Register] Doğrulama e-postası gönderilemedi (%s)", email)
            return Response(
                {"error": "Doğrulama e-postası gönderilemedi. Lütfen tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "message": "Hesap oluşturuldu. E-posta adresinize gönderilen doğrulama kodunu giriniz.",
                "email": email,
                "next_action": "verify",
            },
            status=status.HTTP_201_CREATED,
        )


class RegisterVerifyView(APIView):
    """POST /api/auth/register/verify/ — yeni kaydı doğrula ve login ol."""
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"error": "E-posta ve kod gereklidir."}, status=status.HTTP_400_BAD_REQUEST)

        email = email.lower()
        cached_otp = cache.get(f"otp_reg_{email}")

        # Brute-force protection: Check retry count
        retry_key = f"otp_retry_{email}"
        retries = cache.get(retry_key, 0)
        if retries >= 5:
            cache.delete(f"otp_reg_{email}")  # Invalidate OTP on too many attempts
            return Response({"error": "Çok fazla hatalı deneme. Yeni bir kod istemeniz gerekiyor."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Master OTP Safe Guard: Allowed only in DEBUG mode
        is_master_otp = str(otp) == "000000"
        if is_master_otp:
            if settings.DEBUG:
                import logging
                logging.getLogger(__name__).info(f"Master OTP used for {email} in DEBUG mode.")
            else:
                # In production, 000000 should NEVER work
                is_master_otp = False

        if cached_otp != str(otp) and not is_master_otp:
            cache.set(retry_key, retries + 1, timeout=600)
            return Response({"error": "Geçersiz veya süresi dolmuş kod."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(email=email)
            user.is_active = True
            user.save()
        except User.DoesNotExist:
            return Response({"error": "Kullanıcı bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        # Cache'i temizle
        cache.delete(f"otp_reg_{email}")

        tokens = _get_tokens_for_user(user)

        return Response({
            "message": "Hesap doğrulandı ve giriş yapıldı.",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_200_OK)


class RegisterResendOTPView(APIView):
    """POST /api/auth/register/resend-otp/ — doğrulama kodunu tekrar gönder."""
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "E-posta gereklidir."}, status=status.HTTP_400_BAD_REQUEST)

        email = email.lower()
        
        # Check cooldown (60 seconds)
        if cache.get(f"otp_resend_cooldown_{email}"):
            return Response({"error": "Lütfen yeni bir kod istemeden önce 60 saniye bekleyin."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        if not User.objects.filter(email=email, is_active=False).exists():
            return Response({"error": "Doğrulama bekleyen kullanıcı bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        cache.set(f"otp_reg_{email}", otp_code, timeout=600)
        cache.set(f"otp_resend_cooldown_{email}", True, timeout=60)

        subject = "EcomMarj Hesap Doğrulama Kodu (Tekrar)"
        message = f"Hesabınızı doğrulamak için yeni kodunuz: {otp_code}\n\nBu kod 10 dakika boyunca geçerlidir."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "info@ecommarj.com")

        try:
            send_mail(subject, message, from_email, [email], fail_silently=False)
        except Exception as e:
            return Response({"error": "E-posta gönderilemedi."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"message": "Doğrulama kodu tekrar gönderildi."}, status=status.HTTP_200_OK)


FAIL_LOCKOUT_THRESHOLD = 5
FAIL_LOCKOUT_MINUTES = 15


def _client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
    return xff or request.META.get("REMOTE_ADDR", "0.0.0.0")


def _is_locked_out(user) -> bool:
    """Aktif (locked_until > now) bir AccountLockout var mı?"""
    try:
        from core.models import AccountLockout
        from django.utils import timezone as _tz
        return AccountLockout.objects.filter(user=user, locked_until__gt=_tz.now()).exists()
    except Exception:
        return False


def _record_attempt(user, ip, success, attempt_type="password"):
    try:
        from core.models import LoginAttempt
        LoginAttempt.objects.create(user=user, ip_address=ip, success=success, attempt_type=attempt_type)
    except Exception:
        pass


def _maybe_lock_account(user, ip, reason="Çok fazla başarısız giriş denemesi"):
    """Son 15 dakikadaki başarısız deneme >= eşik ise hesabı kilitle."""
    try:
        from datetime import timedelta as _td
        from django.utils import timezone as _tz
        from core.models import LoginAttempt, AccountLockout
        window_start = _tz.now() - _td(minutes=FAIL_LOCKOUT_MINUTES)
        fails = LoginAttempt.objects.filter(
            user=user, success=False, attempted_at__gte=window_start,
        ).count()
        if fails >= FAIL_LOCKOUT_THRESHOLD:
            AccountLockout.objects.create(
                user=user,
                locked_until=_tz.now() + _td(minutes=FAIL_LOCKOUT_MINUTES),
                reason=reason,
                failed_attempts=fails,
            )
    except Exception:
        pass


class LoginView(APIView):
    """POST /api/auth/login/ — giriş yap."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower()
        password = serializer.validated_data["password"]
        ip = _client_ip(request)

        # Hesabı bul (varsa) — lockout/log kaydı için bilinmesi gerekir
        user_obj = User.objects.filter(email=email).first()

        # Aktif kilit varsa direkt reddet (kullanıcı kayıtlıysa)
        if user_obj and _is_locked_out(user_obj):
            return Response(
                {"errors": {"non_field_errors": [
                    "Çok fazla başarısız giriş denemesi. Hesabınız 15 dakika kilitlendi."
                ]}},
                status=status.HTTP_423_LOCKED,
            )

        user = None
        if user_obj:
            user = authenticate(username=user_obj.username, password=password)

        if user is None:
            # Başarısız denemeyi kaydet ve eşik aşıldıysa kilitle
            _record_attempt(user_obj, ip, success=False)
            if user_obj:
                _maybe_lock_account(user_obj, ip)
            return Response(
                {"errors": {"non_field_errors": ["E-posta veya şifre hatalı."]}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Başarılı — log + last_login_ip
        _record_attempt(user, ip, success=True)
        try:
            from core.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.last_login_ip = ip
            profile.save(update_fields=["last_login_ip"])
        except Exception:
            pass

        tokens = _get_tokens_for_user(user)
        return Response(
            {
                "message": "Giriş başarılı.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class AccessCodeLoginView(APIView):
    """POST /api/auth/access-code/ — admin tarafından üretilmiş kodla giriş.

    OTP zorunluluğu yok; ancak `validate_code` 5 yanlışta IP başına 15dk kilit
    uygular ve hesap askıdaysa giriş yine reddedilir."""
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        code = (request.data or {}).get("code", "")
        ip = _client_ip(request)
        from core.services.access_code_service import validate_code
        ac, err = validate_code(code, ip=ip)
        if err:
            _record_attempt(None, ip, success=False, attempt_type="access_code")
            return Response({"error": err}, status=status.HTTP_401_UNAUTHORIZED)

        user = ac.user
        if not user.is_active:
            return Response({"error": "Hesap pasif durumda."}, status=status.HTTP_403_FORBIDDEN)
        profile = getattr(user, "profile", None)
        if profile and profile.is_suspended:
            return Response(
                {"error": f"Hesabınız askıya alındı: {profile.suspension_reason or '—'}"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if _is_locked_out(user):
            return Response(
                {"error": "Hesap geçici olarak kilitli. 15 dakika sonra tekrar deneyin."},
                status=status.HTTP_423_LOCKED,
            )

        _record_attempt(user, ip, success=True, attempt_type="access_code")
        if profile:
            try:
                profile.last_login_ip = ip
                profile.save(update_fields=["last_login_ip"])
            except Exception:
                pass

        tokens = _get_tokens_for_user(user)
        return Response({
            "message": "Kod ile giriş başarılı.",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    """POST /api/auth/google/ — Google ile giriş yap."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.GOOGLE_OAUTH_CLIENT_IDS:
            logger.error("Google OAuth client id is not configured.")
            return Response(
                {"error": "Google ile giriş şu anda yapılandırılmamış."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            token_info = google_id_token.verify_oauth2_token(
                serializer.validated_data["id_token"],
                google_requests.Request(),
                audience=None,
            )
        except Exception as exc:
            logger.warning("Google token verification failed: %s", exc)
            return Response(
                {"error": "Google doğrulaması başarısız oldu. Lütfen tekrar deneyin."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        audience = str(token_info.get("aud") or "").strip()
        if audience not in settings.GOOGLE_OAUTH_CLIENT_IDS:
            return Response(
                {"error": "Geçersiz Google uygulama kimliği."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not token_info.get("email_verified"):
            return Response(
                {"error": "Google hesabınızın e-posta adresi doğrulanmış olmalıdır."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = str(token_info.get("email") or "").lower().strip()
        if not email:
            return Response({"error": "Google hesabında e-posta bilgisi bulunamadı."}, status=status.HTTP_400_BAD_REQUEST)

        given_name = str(token_info.get("given_name") or "").strip()
        family_name = str(token_info.get("family_name") or "").strip()
        full_name = str(token_info.get("name") or "").strip()

        if not given_name and full_name:
            name_parts = full_name.split(" ", 1)
            given_name = name_parts[0]
            family_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.filter(email=email).first()
        if user:
            updated_fields = []
            if not user.first_name and given_name:
                user.first_name = given_name
                updated_fields.append("first_name")
            if not user.last_name and family_name:
                user.last_name = family_name
                updated_fields.append("last_name")
            if not user.username:
                user.username = email
                updated_fields.append("username")
            if not user.is_active:
                user.is_active = True
                updated_fields.append("is_active")
            if updated_fields:
                user.save(update_fields=updated_fields)
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=given_name,
                last_name=family_name,
                is_active=True,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])

        _ensure_user_profile(user)
        tokens = _get_tokens_for_user(user)

        return Response(
            {
                "message": "Google ile giriş başarılı.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class GoogleOAuthCallbackView(GoogleLoginView):
    """GET/POST /api/auth/google/callback/ — Google OAuth callback endpoint'i."""

    def get(self, request):
        error = request.query_params.get("error")
        if error:
            return Response(
                {"error": "Google giriş işlemi tamamlanamadı.", "detail": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Google OAuth callback route çalışıyor.",
                "login_endpoint": "/api/auth/google/",
                "redirect_uri": "https://www.ecommarj.com/auth/google/callback",
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """GET /api/auth/me/ — mevcut kullanıcı bilgisi."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    """POST /api/auth/logout/ — refresh token'ı blacklist'e alarak oturumu kapat."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from rest_framework_simplejwt.exceptions import TokenError

        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"error": "refresh token gereklidir."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            # Already expired/blacklisted/invalid — desired end state reached.
            pass
        return Response({"message": "Çıkış yapıldı."}, status=status.HTTP_200_OK)


class SendOTPView(APIView):
    """POST /api/auth/send-otp/ — giriş için e-postaya kod gönder."""

    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    # Account-existence is never revealed: the response is identical whether
    # or not the e-mail is registered (prevents user enumeration).
    GENERIC_OK = {"message": "Eğer bu e-posta kayıtlıysa bir doğrulama kodu gönderildi."}

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "E-posta gereklidir."}, status=status.HTTP_400_BAD_REQUEST)

        email = email.lower().strip()

        # 60s cooldown — keyed regardless of account existence so timing
        # cannot be used to enumerate accounts.
        cooldown_key = f"otp_send_cooldown_{email}"
        try:
            if cache.get(cooldown_key):
                return Response(
                    {"error": "Lütfen yeni bir kod istemeden önce 60 saniye bekleyin."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
        except Exception:
            pass  # non-critical, fall through

        user = User.objects.filter(email=email, is_active=True).first()
        if not user:
            # Same response & cooldown as the success path — no enumeration.
            try:
                cache.set(cooldown_key, True, timeout=60)
            except Exception:
                pass
            return Response(self.GENERIC_OK, status=status.HTTP_200_OK)

        # static_otp_code is a fixed per-user login code — only honored in
        # DEBUG. In production it is ignored so it can never act as a backdoor.
        static_code = None
        if settings.DEBUG:
            try:
                from core.models import UserProfile
                profile = UserProfile.objects.get(user__email=email)
                static_code = profile.static_otp_code
            except UserProfile.DoesNotExist:
                static_code = None

        otp_code = static_code or f"{secrets.randbelow(900000) + 100000}"

        try:
            cache.set(f"otp_{email}", otp_code, timeout=300)
            cache.set(cooldown_key, True, timeout=60)
        except Exception as e:
            logger.exception(f"[SendOTP] Redis/cache hatası ({email}): {e}")
            return Response(
                {"error": "Sistem geçici olarak kullanılamıyor. Lütfen tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        subject = "EcomMarj Doğrulama Kodu"
        message = f"Giriş yapmak için doğrulama kodunuz: {otp_code}\n\nBu kod 5 dakika boyunca geçerlidir."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "info@ecommarj.com")

        try:
            send_mail(subject, message, from_email, [email], fail_silently=False)
        except Exception as e:
            logger.exception(f"[SendOTP] SMTP e-posta gönderilemedi ({email}): {e}")
            return Response(
                {"error": "Sistem geçici olarak kullanılamıyor. Lütfen tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            cache.delete(f"otp_login_retry_{email}")
        except Exception:
            pass  # non-critical

        logger.info(f"[SendOTP] OTP gönderildi: {email}")
        return Response(self.GENERIC_OK, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """POST /api/auth/verify-otp/ — kodu doğrula ve giriş yap."""

    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)

        email = request.data.get("email")
        otp = request.data.get("otp")
        
        if not email or not otp:
            return Response({"error": "E-posta ve kod gereklidir."}, status=status.HTTP_400_BAD_REQUEST)
            
        email = email.lower()

        try:
            cached_otp = cache.get(f"otp_{email}")
        except Exception as e:
            logger.exception(f"[VerifyOTP] Redis/cache hatası ({email}): {e}")
            return Response(
                {"error": "Sistem geçici olarak kullanılamıyor. Lütfen tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Brute-force protection: Check retry count
        retry_key = f"otp_login_retry_{email}"
        try:
            retries = cache.get(retry_key, 0)
        except Exception:
            retries = 0

        if retries >= 5:
            try:
                cache.delete(f"otp_{email}")
            except Exception:
                pass
            return Response({"error": "Çok fazla hatalı deneme. Yeni bir kod istemeniz gerekiyor."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Master OTP Safe Guard
        is_master_otp = str(otp) == "000000"
        if is_master_otp:
            if settings.DEBUG:
                logger.info(f"Master login OTP used for {email} in DEBUG mode.")
            else:
                is_master_otp = False

        if cached_otp != str(otp) and not is_master_otp:
            try:
                cache.set(retry_key, retries + 1, timeout=300)
            except Exception:
                pass
            return Response({"error": "Geçersiz veya süresi dolmuş kod."}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Kullanıcıyı bul — yeni kullanıcı yaratma (güvenlik: sadece kayıtlı+aktif kullanıcılar)
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "Kullanıcı bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        
        # Cache'i temizle
        try:
            cache.delete(f"otp_{email}")
        except Exception:
            pass
        
        tokens = _get_tokens_for_user(user)
        
        return Response({
            "message": "Giriş başarılı.",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_200_OK)


class UpdateOnboardingStatusView(APIView):
    """PATCH /api/auth/onboarding/status/ — kullanıcının onboarding durumunu güncelle."""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        status_val = request.data.get("status")
        from core.models import UserProfile
        
        if status_val not in UserProfile.OnboardingStatus.values:
            return Response({"error": "Geçersiz durum."}, status=status.HTTP_400_BAD_REQUEST)
            
        profile = request.user.profile
        profile.onboarding_status = status_val
        profile.save()
        
        return Response({"message": "Durum güncellendi.", "onboarding_status": profile.onboarding_status})
