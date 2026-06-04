"""
ActionItem and ReminderLog models.
"""

import uuid
from django.db import models
from apps.meetings.models import Meeting


class ActionItem(models.Model):
    """Tracks a task assigned during a meeting."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='action_items',
        null=True,
        blank=True,
    )
    task = models.TextField()
    assignee = models.EmailField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    citations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'action_items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task[:60]} [{self.status}]"

    @property
    def is_overdue(self) -> bool:
        """Returns True if due_date has passed and item is not completed."""
        from django.utils import timezone
        return (
            self.due_date is not None
            and self.status != self.Status.COMPLETED
            and self.due_date < timezone.now()
        )


class ReminderLog(models.Model):
    """Records every reminder notification sent for an action item."""

    class DeliveryStatus(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'

    action_item = models.ForeignKey(
        ActionItem,
        on_delete=models.CASCADE,
        related_name='reminder_logs',
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    channel = models.CharField(max_length=50, default='email')
    status = models.CharField(max_length=10, choices=DeliveryStatus.choices)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'reminder_logs'
        ordering = ['-sent_at']

    def __str__(self):
        return f"Reminder [{self.status}] for action_item={self.action_item_id} at {self.sent_at}"
