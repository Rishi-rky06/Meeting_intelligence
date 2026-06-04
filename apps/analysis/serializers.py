"""
Serializers for analysis response data.
"""

from rest_framework import serializers
from apps.analysis.models import MeetingAnalysis


class MeetingAnalysisSerializer(serializers.ModelSerializer):
    """Full meeting analysis response."""

    meetingId = serializers.UUIDField(source='meeting_id')
    analyzedAt = serializers.DateTimeField(source='analyzed_at')

    summary = serializers.SerializerMethodField()
    actionItems = serializers.SerializerMethodField()
    decisions = serializers.SerializerMethodField()
    followUpSuggestions = serializers.SerializerMethodField()

    class Meta:
        model = MeetingAnalysis
        fields = ['id', 'meetingId', 'status', 'analyzedAt', 'summary', 'actionItems', 'decisions', 'followUpSuggestions']

    def _filter_items(self, obj, item_type):
        items = [i for i in obj.items.all() if i.item_type == item_type]
        return [
            {
                'text': i.content,
                'assignee': i.assignee,
                'citations': [
                    {'timestamp': c.timestamp, 'speaker': c.speaker, 'excerpt': c.text_excerpt}
                    for c in i.citations.all()
                ],
            }
            for i in items
        ]

    def get_summary(self, obj) -> list:
        return self._filter_items(obj, 'SUMMARY')

    def get_actionItems(self, obj) -> list:
        return self._filter_items(obj, 'ACTION_ITEM')

    def get_decisions(self, obj) -> list:
        return self._filter_items(obj, 'DECISION')

    def get_followUpSuggestions(self, obj) -> list:
        return self._filter_items(obj, 'FOLLOWUP')
