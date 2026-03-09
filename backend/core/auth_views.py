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
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        tokens = _get_tokens_for_user(user)

        return Response(
            {
                "message": "Hesap başarıyla oluşturuldu.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


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
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            # Plan 1: Auto-register user if they don't exist
            if hasattr(User, 'username'):
                user = User.objects.create_user(username=email, email=email, password=password)
            else:
                user = User.objects.create_user(email=email, password=password)
            user.save()
            # No need to authenticate newly created user, just proceed to token generation

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
