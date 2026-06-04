"""
Meeting CRUD views.
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError, NotFound, MethodNotAllowed
from drf_spectacular.utils import extend_schema

from apps.meetings.models import Meeting, TranscriptSegment
from apps.meetings.serializers import CreateMeetingSerializer, MeetingSerializer, MeetingListSerializer
from core.response import success_response
from core.permissions import IsAuthenticatedViaJWT
from core.pagination import StandardPagination

logger = logging.getLogger(__name__)


@extend_schema(methods=['POST'], request=CreateMeetingSerializer, responses=MeetingSerializer, tags=['meetings'])
@extend_schema(methods=['GET'], responses=MeetingListSerializer, tags=['meetings'])
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticatedViaJWT])
def meetings_collection(request):
    """
    POST /api/meetings  — create a new meeting
    GET  /api/meetings  — list meetings with pagination
    """
    if request.method == 'POST':
        return _create_meeting(request)
    return _list_meetings(request)


def _create_meeting(request):
    """
    Create a new meeting with transcript segments.
    Transcript segments are stored in order (index-based).
    """
    serializer = CreateMeetingSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    data = serializer.validated_data

    meeting = Meeting.objects.create(
        title=data['title'],
        participants=data['participants'],
        meeting_date=data['meetingDate'],
        created_by_id=request.user_id,
    )

    segments = [
        TranscriptSegment(
            meeting=meeting,
            timestamp=seg['timestamp'],
            speaker=seg['speaker'],
            text=seg['text'],
            order=i,
        )
        for i, seg in enumerate(data['transcript'])
    ]
    TranscriptSegment.objects.bulk_create(segments)

    logger.info(f"Meeting created: id={meeting.id} title='{meeting.title}' by user={request.user_id}")

    return success_response(MeetingSerializer(meeting).data, request=request, status=201)


def _list_meetings(request):
    """
    List all meetings created by the authenticated user.
    Supports pagination via ?page= and ?pageSize= query params.
    """
    queryset = Meeting.objects.filter(created_by_id=request.user_id).order_by('-meeting_date')

    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = MeetingListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(operation_id='meetings_retrieve_by_id', responses=MeetingSerializer, tags=['meetings'])
@api_view(['GET'])
@permission_classes([IsAuthenticatedViaJWT])
def get_meeting(request, meeting_id):
    """
    Retrieve a single meeting by ID, including its transcript.
    Only the owner can access their meetings.
    """
    try:
        meeting = Meeting.objects.prefetch_related('transcript_segments').get(
            id=meeting_id,
            created_by_id=request.user_id,
        )
    except Meeting.DoesNotExist:
        raise NotFound('Meeting not found.')

    return success_response(MeetingSerializer(meeting).data, request=request)
