"""
Evaluation endpoint — GET /api/evaluation
"""

from django.urls import path
from django.conf import settings
from django.http import JsonResponse


def evaluation(request):
    """Returns candidate and project metadata for evaluators."""
    return JsonResponse({
        'candidateName': settings.CANDIDATE_NAME,
        'email': settings.CANDIDATE_EMAIL,
        'repositoryUrl': settings.REPOSITORY_URL,
        'deployedUrl': settings.DEPLOYED_URL,
        'externalIntegration': 'Resend Email',
        'features': [
            'Authentication',
            'Meeting Management',
            'AI Analysis with Citations',
            'Action Item Management',
            'Overdue Detection',
            'Reminder Scheduler',
            'Email Integration',
        ],
    })


urlpatterns = [
    path('', evaluation),
]
