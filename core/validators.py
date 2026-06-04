"""
Shared validation helpers used across serializers.
"""

import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def validate_email_address(value: str) -> str:
    """Validate a single email address. Raises DRF ValidationError on failure."""
    try:
        validate_email(value)
    except DjangoValidationError:
        raise ValidationError(f"'{value}' is not a valid email address.")
    return value.lower().strip()


def validate_email_list(emails) -> list:
    """Validate a non-empty list of email addresses."""
    if not isinstance(emails, list) or len(emails) == 0:
        raise ValidationError("participants must be a non-empty list of email addresses.")
    return [validate_email_address(e) for e in emails]
