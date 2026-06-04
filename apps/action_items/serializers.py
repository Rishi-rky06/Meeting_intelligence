"""
Serializers for action item endpoints.
"""

from rest_framework import serializers
from apps.action_items.models import ActionItem
from core.validators import validate_email_address


class CreateActionItemSerializer(serializers.Serializer):
    """Validates the create-action-item payload."""

    meetingId = serializers.UUIDField(required=False, allow_null=True)
    task = serializers.CharField(min_length=1)
    assignee = serializers.EmailField(required=False, allow_blank=True, default='')
    dueDate = serializers.DateTimeField(required=False, allow_null=True)
    citations = serializers.ListField(required=False, default=list)

    def validate_assignee(self, value: str) -> str:
        if value:
            return validate_email_address(value)
        return value


class UpdateStatusSerializer(serializers.Serializer):
    """Validates a status update payload."""

    status = serializers.ChoiceField(choices=ActionItem.Status.choices)


class ActionItemSerializer(serializers.ModelSerializer):
    """Full action item representation."""

    meetingId = serializers.UUIDField(source='meeting_id', read_only=True)
    dueDate = serializers.DateTimeField(source='due_date', allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    isOverdue = serializers.SerializerMethodField()

    class Meta:
        model = ActionItem
        fields = ['id', 'meetingId', 'task', 'assignee', 'dueDate', 'status', 'citations', 'createdAt', 'isOverdue']

    def get_isOverdue(self, obj) -> bool:
        return obj.is_overdue
