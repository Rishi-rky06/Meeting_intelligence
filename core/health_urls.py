"""
Health check endpoint — GET /health
"""

from django.urls import path
from django.http import JsonResponse


def health(request):
    """Returns a simple UP status."""
    return JsonResponse({'status': 'UP'})


urlpatterns = [
    path('', health),
]
