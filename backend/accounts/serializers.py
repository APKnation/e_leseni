from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    lga_name = serializers.CharField(source='lga.name', read_only=True, default=None)
    has_nida = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'role', 'phone_number', 'nida_number', 'has_nida', 'lga', 'lga_name', 'is_lga_staff',
        ]
        read_only_fields = ['id', 'is_lga_staff', 'lga_name', 'has_nida']

    def get_has_nida(self, obj):
        """Frontends show a NIDA checkmark without exposing the full number."""
        return bool(obj.nida_number)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    nida_number = serializers.CharField(required=False, allow_blank=True, max_length=20)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'phone_number', 'nida_number', 'password']

    def validate_nida_number(self, value):
        """NIDA is 20 digits when provided (users can add it later)."""
        value = (value or '').strip()
        if value and not value.isdigit():
            raise serializers.ValidationError('NIDA number must contain only digits (20 digits).')
        if value and len(value) != 20:
            raise serializers.ValidationError('NIDA number must be exactly 20 digits.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Self-service profile fields (used by PATCH /api/auth/me/update/)."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'nida_number']

    def validate_nida_number(self, value):
        value = (value or '').strip()
        if value and (not value.isdigit() or len(value) != 20):
            raise serializers.ValidationError('NIDA number must be exactly 20 digits.')
        return value


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
