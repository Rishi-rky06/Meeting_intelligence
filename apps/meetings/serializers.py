"""
Serializers for meeting endpoints.
"""

from rest_framework import serializers
from apps.meetings.models import Meeting, TranscriptSegment
from core.validators import validate_email_list


class TranscriptSegmentSerializer(serializers.ModelSerializer):
    """Serializes/deserializes a single transcript segment."""

    class Meta:
        model = TranscriptSegment
        fields = ['timestamp', 'speaker', 'text']

    def validate_timestamp(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError('timestamp is required.')
        return value.strip()

    def validate_speaker(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError('speaker is required.')
        return value.strip()

    def validate_text(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError('text is required.')
        return value.strip()


class CreateMeetingSerializer(serializers.Serializer):
    """Validates the create-meeting payload."""

    title = serializers.CharField(max_length=500, min_length=1)
    participants = serializers.ListField(child=serializers.CharField(), min_length=1)
    meetingDate = serializers.DateTimeField()
    transcript = serializers.ListField(
        child=TranscriptSegmentSerializer(),
        min_length=1,
    )

    def validate_participants(self, value: list) -> list:
        return validate_email_list(value)

    def validate_transcript(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError('At least one transcript segment is required.')
        return value


class MeetingSerializer(serializers.ModelSerializer):
    """Full meeting representation including transcript."""

    transcript = TranscriptSegmentSerializer(source='transcript_segments', many=True, read_only=True)
    createdBy = serializers.UUIDField(source='created_by_id', read_only=True)
    meetingDate = serializers.DateTimeField(source='meeting_date')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Meeting
        fields = ['id', 'title', 'participants', 'meetingDate', 'createdBy', 'createdAt', 'transcript']


class MeetingListSerializer(serializers.ModelSerializer):
    """Lightweight meeting representation for list views (no transcript)."""

    createdBy = serializers.UUIDField(source='created_by_id', read_only=True)
    meetingDate = serializers.DateTimeField(source='meeting_date')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Meeting
        fields = ['id', 'title', 'participants', 'meetingDate', 'createdBy', 'createdAt']
