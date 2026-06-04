"""
Action item CRUD, status update, and overdue views.
"""

import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError, NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.action_items.models import ActionItem
from apps.action_items.serializers import (
    CreateActionItemSerializer,
    UpdateStatusSerializer,
    ActionItemSerializer,
)
from apps.meetings.models import Meeting
from core.response import success_response
from core.permissions import IsAuthenticatedViaJWT
from core.pagination import StandardPagination

logger = logging.getLogger(__name__)


@extend_schema(
    methods=['POST'],
    request=CreateActionItemSerializer,
    responses=ActionItemSerializer,
    tags=['action-items'],
)
@extend_schema(
    methods=['GET'],
    responses=ActionItemSerializer,
    parameters=[
        OpenApiParameter('status', str, description='Filter by status: PENDING, IN_PROGRESS, COMPLETED'),
        OpenApiParameter('assignee', str, description='Filter by assignee email'),
        OpenApiParameter('meetingId', str, description='Filter by meeting UUID'),
    ],
    tags=['action-items'],
)
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticatedViaJWT])
def action_items_collection(request):
    """
    POST /api/action-items  — create a new action item
    GET  /api/action-items  — list action items with optional filters
    """
    if request.method == 'POST':
        return _create_action_item(request)
    return _list_action_items(request)


def _create_action_item(request):
    """
    Create a manual action item.
    meetingId is optional; if provided the meeting must belong to the authenticated user.
    """
    serializer = CreateActionItemSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    data = serializer.validated_data
    meeting = None

    if data.get('meetingId'):
        try:
            meeting = Meeting.objects.get(id=data['meetingId'], created_by_id=request.user_id)
        except Meeting.DoesNotExist:
            raise NotFound('Meeting not found.')

    item = ActionItem.objects.create(
        meeting=meeting,
        task=data['task'],
        assignee=data.get('assignee', ''),
        due_date=data.get('dueDate'),
        citations=data.get('citations', []),
    )

    logger.info(f"ActionItem created: id={item.id} task='{item.task[:40]}' by user={request.user_id}")
    return success_response(ActionItemSerializer(item).data, request=request, status=201)


def _list_action_items(request):
    """
    List action items.
    Supports filtering: ?status=PENDING, ?assignee=email, ?meetingId=uuid
    """
    queryset = ActionItem.objects.all()

    # Scope to items that belong to meetings owned by this user, or unattached items
    user_meeting_ids = Meeting.objects.filter(
        created_by_id=request.user_id
    ).values_list('id', flat=True)
    queryset = queryset.filter(meeting_id__in=user_meeting_ids) | queryset.filter(meeting__isnull=True)

    status_filter = request.query_params.get('status')
    if status_filter:
        if status_filter not in ActionItem.Status.values:
            raise ValidationError({'status': f"Invalid status. Choose from {ActionItem.Status.values}"})
        queryset = queryset.filter(status=status_filter)

    assignee_filter = request.query_params.get('assignee')
    if assignee_filter:
        queryset = queryset.filter(assignee__iexact=assignee_filter)

    meeting_id_filter = request.query_params.get('meetingId')
    if meeting_id_filter:
        queryset = queryset.filter(meeting_id=meeting_id_filter)

    queryset = queryset.order_by('-created_at')

    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ActionItemSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(request=UpdateStatusSerializer, responses=ActionItemSerializer, tags=['action-items'])
@api_view(['PATCH'])
@permission_classes([IsAuthenticatedViaJWT])
def update_status(request, item_id):
    """
    Update the status of an action item.
    Supported statuses: PENDING, IN_PROGRESS, COMPLETED.
    """
    serializer = UpdateStatusSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    item = _get_action_item(item_id, request.user_id)
    old_status = item.status
    item.status = serializer.validated_data['status']
    item.save(update_fields=['status'])

    logger.info(f"ActionItem id={item.id} status updated: {old_status} -> {item.status}")
    return success_response(ActionItemSerializer(item).data, request=request)


@extend_schema(responses=ActionItemSerializer, tags=['action-items'])
@api_view(['GET'])
@permission_classes([IsAuthenticatedViaJWT])
def get_overdue(request):
    """
    Return all overdue action items for the authenticated user's meetings.
    An item is overdue when status != COMPLETED and due_date < now().
    """
    user_meeting_ids = Meeting.objects.filter(
        created_by_id=request.user_id
    ).values_list('id', flat=True)

    now = timezone.now()
    queryset = ActionItem.objects.filter(
        meeting_id__in=user_meeting_ids,
        due_date__lt=now,
    ).exclude(status=ActionItem.Status.COMPLETED).order_by('due_date')

    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ActionItemSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


def _get_action_item(item_id, user_id) -> ActionItem:
    """Fetch an action item that belongs to a meeting owned by user_id."""
    user_meeting_ids = Meeting.objects.filter(
        created_by_id=user_id
    ).values_list('id', flat=True)

    try:
        return ActionItem.objects.get(
            id=item_id,
            meeting_id__in=user_meeting_ids,
        )
    except ActionItem.DoesNotExist:
        raise NotFound('Action item not found.')
