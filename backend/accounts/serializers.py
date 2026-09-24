from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PasswordResetToken, User


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


class PasswordResetRequestSerializer(serializers.Serializer):
    """Step 1: identify the account by username + phone number."""

    username = serializers.CharField()
    phone_number = serializers.CharField()

    def validate(self, attrs):
        try:
            user = User.objects.get(
                username=attrs['username'],
                phone_number=attrs['phone_number'],
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'No account found with that username and phone number.'
            )
        attrs['user'] = user
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Step 2: validate the token and set a new password."""

    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Invalid or expired reset token.')
        if not reset_token.is_valid:
            raise serializers.ValidationError('This reset token has expired or already been used.')
        self._reset_token = reset_token
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self):
        reset_token = self._reset_token
        user = reset_token.user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        reset_token.used = True
        reset_token.save(update_fields=['used'])
        return user
