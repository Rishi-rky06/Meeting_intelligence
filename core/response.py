"""
Unified API response helpers.
All responses follow: { traceId, success, data } or { traceId, success, error }
"""

from rest_framework.response import Response


def success_response(data, request=None, status=200):
    """Return a standardised success envelope."""
    trace_id = getattr(request, 'trace_id', '-') if request else '-'
    return Response(
        {
            'traceId': trace_id,
            'success': True,
            'data': data,
        },
        status=status,
    )


def error_response(code: str, message: str, request=None, status=400):
    """Return a standardised error envelope."""
    trace_id = getattr(request, 'trace_id', '-') if request else '-'
    return Response(
        {
            'traceId': trace_id,
            'success': False,
            'error': {
                'code': code,
                'message': message,
            },
        },
        status=status,
    )
