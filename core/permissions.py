"""
DRF permission class that enforces JWT authentication.
"""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated


class IsAuthenticatedViaJWT(BasePermission):
    """
    Grants access only if JWTAuthMiddleware successfully decoded an access token.
    Returns 401 for missing/invalid tokens.
    """

    def has_permission(self, request, view):
        if request.auth_error:
            raise AuthenticationFailed(request.auth_error)
        if not request.user_id:
            raise NotAuthenticated('Authentication credentials were not provided.')
        return True
