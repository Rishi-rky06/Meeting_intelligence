"""
JWT authentication middleware.
Reads 'Authorization: Bearer <token>', decodes it, and attaches the user to request.
Sets request.user and request.auth_error for views to use.
"""

import logging
import jwt
from apps.authentication.utils import decode_token

logger = logging.getLogger(__name__)

_PUBLIC_PATHS = {
    '/api/auth/register',
    '/api/auth/login',
    '/api/auth/refresh',
    '/health',
    '/api/evaluation',
    '/api/schema/',
    '/api/docs/',
    '/api/redoc/',
}


class JWTAuthMiddleware:
    """
    Processes Authorization header on every request.
    Attaches request.user_id if token is valid; sets request.auth_error otherwise.
    Does not block public routes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id = None
        request.auth_error = None

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Bearer '):
            token = auth_header[len('Bearer '):]
            try:
                payload = decode_token(token)
                if payload.get('type') != 'access':
                    request.auth_error = 'Token type must be access.'
                else:
                    request.user_id = payload['sub']
            except jwt.ExpiredSignatureError:
                request.auth_error = 'Token has expired.'
            except jwt.InvalidTokenError as exc:
                request.auth_error = f'Invalid token: {exc}'

        return self.get_response(request)
