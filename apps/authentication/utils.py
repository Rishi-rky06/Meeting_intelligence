"""
JWT token generation and decoding utilities.
Uses PyJWT directly — no third-party auth library.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta

import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

_ALGORITHM = settings.JWT_ALGORITHM


def generate_tokens(user_id: str) -> dict:
    """
    Generate a new access/refresh token pair for a user.

    Returns:
        { 'access': '<token>', 'refresh': '<token>' }
    """
    now = datetime.now(tz=timezone.utc)

    access_payload = {
        'sub': str(user_id),
        'type': 'access',
        'iat': now,
        'exp': now + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRY_HOURS),
        'jti': str(uuid.uuid4()),
    }

    refresh_payload = {
        'sub': str(user_id),
        'type': 'refresh',
        'iat': now,
        'exp': now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRY_DAYS),
        'jti': str(uuid.uuid4()),
    }

    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)

    return {'access': access_token, 'refresh': refresh_token}


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Returns the payload dict on success.
    Raises jwt.PyJWTError subclasses on failure (expired, invalid, etc.).
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
