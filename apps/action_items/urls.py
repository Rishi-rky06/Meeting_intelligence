"""
Action item URL routes.
"""

from django.urls import path
from apps.action_items import views

urlpatterns = [
    path('', views.action_items_collection, name='action-items-collection'),
    path('overdue', views.get_overdue, name='action-items-overdue'),
    path('<uuid:item_id>/status', views.update_status, name='action-item-status'),
]
