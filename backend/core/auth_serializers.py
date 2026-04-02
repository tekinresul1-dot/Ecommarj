"""
Auth serializers for EcomMarj registration and login.
"""

from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    """Kayıt formu serializer'ı - Üretim odaklı güncellenmiş alanlar."""

    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(min_length=8, write_only=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="", allow_null=True)
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="", allow_null=True)
    kvkk_terms_accepted = serializers.BooleanField()

    def validate_kvkk_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError("Koşulları kabul etmelisiniz.")
        return value

    def validate_email(self, value):
        from django.contrib.auth.models import User
        email = value.lower().strip()
        
        # Check for active (verified) user
        if User.objects.filter(email=email, is_active=True).exists():
            raise serializers.ValidationError({
                "email": {
                    "code": "EMAIL_ALREADY_EXISTS",
                    "message": "Bu e-posta adresi ile zaten aktif bir hesap bulunmaktadır.",
                    "next_action": "login"
                }
            })
            
        # Check for inactive (unverified) user
        if User.objects.filter(email=email, is_active=False).exists():
            raise serializers.ValidationError({
                "email": {
                    "code": "EMAIL_EXISTS_UNVERIFIED",
                    "message": "Bu e-posta adresi kayıtlı ancak henüz doğrulanmamış.",
                    "next_action": "verify_or_resend"
                }
            })
            
        return email

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Şifreler eşleşmiyor."})
        return data

    def create(self, validated_data):
        from django.contrib.auth.models import User
        from core.models import UserProfile, Organization
        
        email = validated_data["email"]
        full_name = validated_data["full_name"].strip()
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        user = User.objects.filter(email=email).first()
        if user:
            # Update existing user (e.g. previously unverified)
            user.set_password(validated_data["password"])
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.save()
        else:
            # Create new user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=validated_data["password"],
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )

        # Handle Organization and Profile
        company_name = validated_data.get("company_name") or f"{first_name} {last_name} Firması".strip()
        
        profile = getattr(user, "profile", None)
        if profile and profile.organization:
            org = profile.organization
            org.name = company_name
            org.save()
        else:
            org = Organization.objects.create(name=company_name)

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "organization": org,
                "phone": validated_data.get("phone", ""),
                "company": validated_data.get("company_name", ""),
            }
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Giriş formu serializer'ı."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class GoogleLoginSerializer(serializers.Serializer):
    """Google Identity token giriş serializer'ı."""

    id_token = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Kullanıcı bilgi serializer'ı."""

    phone = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    onboarding_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "phone", "company", "onboarding_status", "date_joined"]
        read_only_fields = fields

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_phone(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.phone if profile else ""

    def get_company(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.company if profile else ""

    def get_onboarding_status(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.onboarding_status if profile else "WELCOME"
