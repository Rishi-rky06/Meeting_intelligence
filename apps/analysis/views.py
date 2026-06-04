"""
Meeting analysis view — triggers AI analysis for a meeting.
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from apps.analysis.models import MeetingAnalysis
from apps.analysis.serializers import MeetingAnalysisSerializer
from apps.analysis.services.claude_service import analyze_meeting
from apps.meetings.models import Meeting
from core.response import success_response, error_response
from core.permissions import IsAuthenticatedViaJWT

logger = logging.getLogger(__name__)


@extend_schema(request=None, responses=MeetingAnalysisSerializer, tags=['analysis'])
@api_view(['POST'])
@permission_classes([IsAuthenticatedViaJWT])
def analyze_meeting_view(request, meeting_id):
    """
    Trigger AI analysis for a meeting.
    Calls Claude API, saves results, and returns the full analysis.
    Re-analyzing an existing meeting replaces the previous results.
    """
    try:
        meeting = Meeting.objects.prefetch_related('transcript_segments').get(
            id=meeting_id,
            created_by_id=request.user_id,
        )
    except Meeting.DoesNotExist:
        raise NotFound('Meeting not found.')

    if not meeting.transcript_segments.exists():
        return error_response(
            'NO_TRANSCRIPT',
            'Cannot analyze a meeting with no transcript.',
            request,
            status=422,
        )

    try:
        analysis = analyze_meeting(meeting)
    except Exception as exc:
        logger.error(f"Analysis failed for meeting id={meeting_id}: {exc}")
        try:
            analysis = MeetingAnalysis.objects.prefetch_related(
                'items__citations'
            ).get(meeting=meeting)
        except MeetingAnalysis.DoesNotExist:
            return error_response('ANALYSIS_FAILED', str(exc), request, status=500)
        return error_response('ANALYSIS_FAILED', str(exc), request, status=500)

    analysis = MeetingAnalysis.objects.prefetch_related('items__citations').get(id=analysis.id)
    return success_response(MeetingAnalysisSerializer(analysis).data, request=request)
