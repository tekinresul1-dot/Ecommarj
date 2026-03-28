"""
Auth views for EcomMarj — register, login, me.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .auth_serializers import RegisterSerializer, LoginSerializer, UserSerializer
import secrets
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
def _get_tokens_for_user(user):
    """Generate JWT token pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RegisterView(APIView):
    """POST /api/auth/register/ — yeni hesap oluştur."""

    permission_classes = [AllowAny]

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
        
        # Generate OTP for registration verification
        email = user.email.lower()
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        
        # Store OTP in cache for 10 minutes
        cache.set(f"otp_reg_{email}", otp_code, timeout=600)
        
        # Send OTP email
        subject = "EcomMarj Hesap Doğrulama Kodu"
        message = f"EcomMarj hesabınızı doğrulamak için kodunuz: {otp_code}\n\nBu kod 10 dakika boyunca geçerlidir."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "info@ecommarj.com")
        
        try:
            send_mail(subject, message, from_email, [email], fail_silently=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Registration OTP email failed ({email}): {e}")
            # We still return success as the user is created, but warn about email failure?
            # Or perhaps delete user and return error? 
            # Given requirements, let's just log and continue, user can 'resend'.

        return Response(
            {
                "message": "Hesap oluşturuldu. Lütfen e-posta adresinize gönderilen doğrulama kodunu girin.",
                "email": email,
            },
            status=status.HTTP_201_CREATED,
        )


class RegisterVerifyView(APIView):
    """POST /api/auth/register/verify/ — yeni kaydı doğrula ve login ol."""
    permission_classes = [AllowAny]

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


class LoginView(APIView):
    """POST /api/auth/login/ — giriş yap."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower()
        password = serializer.validated_data["password"]

        # Django default User uses username for auth, we use email as username
        user = None
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass  # user stays None → 401 below

        if user is None:
            return Response(
                {"errors": {"non_field_errors": ["E-posta veya şifre hatalı."]}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = _get_tokens_for_user(user)

        return Response(
            {
                "message": "Giriş başarılı.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """GET /api/auth/me/ — mevcut kullanıcı bilgisi."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class SendOTPView(APIView):
    """POST /api/auth/send-otp/ — giriş için e-postaya kod gönder."""

    permission_classes = [AllowAny]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)

        email = request.data.get("email")
        if not email:
            return Response({"error": "E-posta gereklidir."}, status=status.HTTP_400_BAD_REQUEST)

        email = email.lower()

        if not User.objects.filter(email=email, is_active=True).exists():
            return Response(
                {"error": "Bu e-posta adresi sistemde kayıtlı değil."},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp_code = f"{secrets.randbelow(900000) + 100000}"

        # OTP'yi cache'e yaz (Redis). Başarısız olursa 503 dön.
        try:
            cache.set(f"otp_{email}", otp_code, timeout=300)
        except Exception as e:
            logger.exception(f"[SendOTP] Redis/cache hatası ({email}): {e}")
            return Response(
                {"error": "Sistem geçici olarak kullanılamıyor. Lütfen tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # E-posta gönderme
        subject = "EcomMarj Doğrulama Kodu"
        message = f"Giriş yapmak için doğrulama kodunuz: {otp_code}\n\nBu kod 5 dakika boyunca geçerlidir."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "info@ecommarj.com")

        try:
            send_mail(subject, message, from_email, [email], fail_silently=False)
        except Exception as e:
            logger.exception(f"[SendOTP] SMTP e-posta gönderilemedi ({email}): {e}")
            return Response(
                {"error": "E-posta gönderilemedi. Lütfen daha sonra tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Reset retry count if resending code
        try:
            cache.delete(f"otp_retry_{email}")
        except Exception:
            pass  # non-critical

        logger.info(f"[SendOTP] OTP başarıyla gönderildi: {email}")
        return Response({"message": "Doğrulama kodu e-posta adresinize gönderildi."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """POST /api/auth/verify-otp/ — kodu doğrula ve giriş yap."""

    permission_classes = [AllowAny]

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
