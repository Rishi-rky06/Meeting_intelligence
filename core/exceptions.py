"""
Global DRF exception handler — converts all exceptions to the unified response format.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError, AuthenticationFailed, NotAuthenticated,
    PermissionDenied, NotFound, MethodNotAllowed,
)
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    NotAuthenticated: status.HTTP_401_UNAUTHORIZED,
    AuthenticationFailed: status.HTTP_401_UNAUTHORIZED,
    PermissionDenied: status.HTTP_403_FORBIDDEN,
    DjangoPermissionDenied: status.HTTP_403_FORBIDDEN,
    NotFound: status.HTTP_404_NOT_FOUND,
    Http404: status.HTTP_404_NOT_FOUND,
    MethodNotAllowed: status.HTTP_405_METHOD_NOT_ALLOWED,
}

_CODE_MAP = {
    ValidationError: 'VALIDATION_ERROR',
    NotAuthenticated: 'UNAUTHORIZED',
    AuthenticationFailed: 'UNAUTHORIZED',
    PermissionDenied: 'FORBIDDEN',
    DjangoPermissionDenied: 'FORBIDDEN',
    NotFound: 'NOT_FOUND',
    Http404: 'NOT_FOUND',
    MethodNotAllowed: 'METHOD_NOT_ALLOWED',
}


def _flatten_errors(detail) -> str:
    """Recursively flatten DRF validation error detail into a readable string."""
    if isinstance(detail, list):
        return ' '.join(_flatten_errors(d) for d in detail)
    if isinstance(detail, dict):
        parts = []
        for field, errors in detail.items():
            parts.append(f"{field}: {_flatten_errors(errors)}")
        return ' | '.join(parts)
    return str(detail)


def global_exception_handler(exc, context):
    """
    Intercepts every DRF exception and re-shapes it into the unified envelope.
    Unhandled exceptions return a generic 500.
    """
    request = context.get('request')
    trace_id = getattr(request, 'trace_id', '-') if request else '-'

    drf_response = exception_handler(exc, context)

    http_status = _STATUS_MAP.get(type(exc))
    error_code = _CODE_MAP.get(type(exc), 'SERVER_ERROR')

    if isinstance(exc, ValidationError):
        message = _flatten_errors(exc.detail)
        http_status = http_status or status.HTTP_400_BAD_REQUEST
    elif drf_response is not None:
        message = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
        http_status = http_status or drf_response.status_code
    else:
        logger.exception(f"Unhandled exception: {exc}")
        message = 'An unexpected error occurred.'
        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = 'SERVER_ERROR'

    from rest_framework.response import Response
    return Response(
        {
            'traceId': trace_id,
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
            },
        },
        status=http_status,
    )
