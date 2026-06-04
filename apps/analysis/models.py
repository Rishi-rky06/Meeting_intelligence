"""
Models for AI-generated meeting analysis results.
"""

from django.db import models
from apps.meetings.models import Meeting


class MeetingAnalysis(models.Model):
    """Stores the overall analysis state and raw AI response for a meeting."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='analysis',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    raw_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'meeting_analyses'

    def __str__(self):
        return f"Analysis for {self.meeting.title} [{self.status}]"


class AnalysisItem(models.Model):
    """A single AI-generated insight (summary point, action item, decision, or follow-up)."""

    class ItemType(models.TextChoices):
        SUMMARY = 'SUMMARY', 'Summary'
        ACTION_ITEM = 'ACTION_ITEM', 'Action Item'
        DECISION = 'DECISION', 'Decision'
        FOLLOWUP = 'FOLLOWUP', 'Follow-up Suggestion'

    analysis = models.ForeignKey(
        MeetingAnalysis,
        on_delete=models.CASCADE,
        related_name='items',
    )
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    content = models.TextField()
    assignee = models.EmailField(null=True, blank=True)

    class Meta:
        db_table = 'analysis_items'

    def __str__(self):
        return f"[{self.item_type}] {self.content[:60]}"


class Citation(models.Model):
    """A transcript citation backing a single AnalysisItem."""

    analysis_item = models.ForeignKey(
        AnalysisItem,
        on_delete=models.CASCADE,
        related_name='citations',
    )
    timestamp = models.CharField(max_length=20)
    speaker = models.CharField(max_length=255, blank=True)
    text_excerpt = models.TextField(blank=True)

    class Meta:
        db_table = 'citations'

    def __str__(self):
        return f"Citation [{self.timestamp}] by {self.speaker}"
