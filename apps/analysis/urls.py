"""
Analysis URL routes — mounted at /api/
"""

from django.urls import path
from apps.analysis import views

urlpatterns = [
    path('meetings/<uuid:meeting_id>/analyze', views.analyze_meeting_view, name='meeting-analyze'),
]
