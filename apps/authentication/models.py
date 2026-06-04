"""
Custom User model — UUID primary key, email-based login, no username.
"""

import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    """Manager for the custom User model."""

    def create_user(self, email: str, name: str, password: str, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, name: str, password: str, **extra_fields):
        """Create a superuser (used for management commands)."""
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser):
    """
    Application user.
    Uses email as the unique login identifier.
    Password is stored via Django's PBKDF2 hasher.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    def check_password(self, raw_password: str) -> bool:
        """Verify raw password against the stored hash."""
        return django_check_password(raw_password, self.password)
