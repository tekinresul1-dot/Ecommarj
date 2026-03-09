"""
Auth serializers for EcomMarj registration and login.
"""

from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    """Kayıt formu serializer'ı."""

    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(min_length=8, write_only=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    company = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu e-posta adresi zaten kayıtlı.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu e-posta adresi zaten kayıtlı.")
        return value.lower()

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Şifreler eşleşmiyor."})
        return data

    def create(self, validated_data):
        name_parts = validated_data["name"].strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
        )

        from core.models import UserProfile, Organization

        # Create tenant (Organization)
        company_name = validated_data.get("company") or f"{first_name} {last_name} Firması".strip()
        org = Organization.objects.create(name=company_name)

        UserProfile.objects.create(
            user=user,
            organization=org,
            phone=validated_data.get("phone", ""),
            company=validated_data.get("company", ""),
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Giriş formu serializer'ı."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Kullanıcı bilgi serializer'ı."""

    phone = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "phone", "company", "date_joined"]
        read_only_fields = fields

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_phone(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.phone if profile else ""

    def get_company(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.company if profile else ""
