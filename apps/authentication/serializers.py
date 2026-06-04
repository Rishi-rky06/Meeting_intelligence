"""
Serializers for authentication endpoints.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.authentication.models import User


class RegisterSerializer(serializers.Serializer):
    """Validates registration input."""

    name = serializers.CharField(max_length=255, min_length=1)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value: str) -> str:
        """Ensure the email is not already registered."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_password(self, value: str) -> str:
        """Run Django's built-in password validators."""
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data: dict) -> User:
        """Create and return a new user."""
        return User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
        )


class LoginSerializer(serializers.Serializer):
    """Validates login credentials."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value: str) -> str:
        return value.lower()


class RefreshSerializer(serializers.Serializer):
    """Accepts a refresh token."""

    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a user."""

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'created_at']
        read_only_fields = fields
