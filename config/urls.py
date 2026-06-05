"""
Root URL configuration.
"""

from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('', include('core.root_urls')),
    path('health', include('core.health_urls')),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/meetings/', include('apps.meetings.urls')),
    path('api/', include('apps.analysis.urls')),
    path('api/action-items/', include('apps.action_items.urls')),
    path('api/evaluation', include('core.evaluation_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
