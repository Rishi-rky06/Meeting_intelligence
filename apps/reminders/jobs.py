"""
Background job: detect overdue action items and send email reminders.
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_overdue_reminders():
    """
    Find all overdue action items, send a reminder email for each,
    and record the attempt in ReminderLog.

    An item is overdue when:
      - status != COMPLETED
      - due_date < now()
    """
    from apps.action_items.models import ActionItem, ReminderLog
    from apps.reminders.integrations.email_service import send_reminder_email

    now = timezone.now()

    overdue_items = ActionItem.objects.filter(
        due_date__lt=now,
    ).exclude(
        status=ActionItem.Status.COMPLETED,
    ).select_related('meeting')

    count = overdue_items.count()
    if count == 0:
        logger.info("Reminder job: no overdue action items found.")
        return

    logger.info(f"Reminder job: processing {count} overdue action item(s).")

    for item in overdue_items:
        success = send_reminder_email(item)

        ReminderLog.objects.create(
            action_item=item,
            channel='email',
            status=ReminderLog.DeliveryStatus.SUCCESS if success else ReminderLog.DeliveryStatus.FAILED,
            error_message=None if success else 'Email delivery failed — see logs for details.',
        )

    logger.info(f"Reminder job: completed processing {count} item(s).")
