"""
Root endpoint — GET /
Returns a friendly JSON welcome page listing the key API URLs, so the bare
deployment URL shows something useful instead of a 404.
"""

from django.urls import path
from django.http import JsonResponse


def root(request):
    """Return a welcome message with links to the main endpoints."""
    base = request.build_absolute_uri('/').rstrip('/')
    return JsonResponse({
        'service': 'Meeting Intelligence Service',
        'status': 'running',
        'documentation': f'{base}/api/docs/',
        'endpoints': {
            'health': f'{base}/health',
            'swaggerDocs': f'{base}/api/docs/',
            'openapiSchema': f'{base}/api/schema/',
            'redoc': f'{base}/api/redoc/',
            'evaluation': f'{base}/api/evaluation',
            'auth': f'{base}/api/auth/',
            'meetings': f'{base}/api/meetings/',
            'actionItems': f'{base}/api/action-items/',
        },
    })


urlpatterns = [
    path('', root),
]
