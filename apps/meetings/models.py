"""
Meeting and TranscriptSegment models.
"""

import uuid
from django.db import models
from django.conf import settings


class Meeting(models.Model):
    """Stores a meeting record with participants and metadata."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    participants = models.JSONField(default=list)
    meeting_date = models.DateTimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meetings',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meetings'
        ordering = ['-meeting_date']

    def __str__(self):
        return self.title


class TranscriptSegment(models.Model):
    """A single line of dialogue within a meeting transcript."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='transcript_segments',
    )
    timestamp = models.CharField(max_length=20)
    speaker = models.CharField(max_length=255)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'transcript_segments'
        ordering = ['order', 'id']

    def __str__(self):
        return f"[{self.timestamp}] {self.speaker}: {self.text[:50]}"
