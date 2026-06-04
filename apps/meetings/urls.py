"""
Meeting URL routes.
"""

from django.urls import path
from apps.meetings import views

urlpatterns = [
    path('', views.meetings_collection, name='meetings-collection'),
    path('<uuid:meeting_id>', views.get_meeting, name='meeting-detail'),
]
