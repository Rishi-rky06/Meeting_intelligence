"""
Resend email integration for overdue action item reminders.
"""

import logging
import resend
from django.conf import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


def send_reminder_email(action_item) -> bool:
    """
    Send an overdue reminder email via Resend.

    Args:
        action_item: ActionItem model instance

    Returns:
        True if email was sent successfully, False otherwise.
    """
    meeting_title = action_item.meeting.title if action_item.meeting else 'N/A'
    due_date_str = (
        action_item.due_date.strftime('%Y-%m-%d %H:%M UTC')
        if action_item.due_date
        else 'No due date set'
    )

    to_email = action_item.assignee or settings.RESEND_FROM_EMAIL

    subject = f"Reminder: Action Item Overdue — {action_item.task[:60]}"

    html_body = f"""
    <h2>Action Item Overdue Reminder</h2>
    <table>
      <tr><td><strong>Task:</strong></td><td>{action_item.task}</td></tr>
      <tr><td><strong>Assigned To:</strong></td><td>{action_item.assignee or 'Unassigned'}</td></tr>
      <tr><td><strong>Due Date:</strong></td><td>{due_date_str}</td></tr>
      <tr><td><strong>Meeting:</strong></td><td>{meeting_title}</td></tr>
      <tr><td><strong>Status:</strong></td><td>{action_item.status}</td></tr>
    </table>
    <p>Please update the status of this action item as soon as possible.</p>
    """

    text_body = (
        f"Reminder: Action Item Overdue\n\n"
        f"Task: {action_item.task}\n"
        f"Assigned To: {action_item.assignee or 'Unassigned'}\n"
        f"Due Date: {due_date_str}\n"
        f"Meeting: {meeting_title}\n"
        f"Status: {action_item.status}\n"
    )

    try:
        params = {
            'from': settings.RESEND_FROM_EMAIL,
            'to': [to_email],
            'subject': subject,
            'html': html_body,
            'text': text_body,
        }
        resend.Emails.send(params)
        logger.info(f"Reminder email sent for action_item id={action_item.id} to={to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send reminder email for action_item id={action_item.id}: {exc}")
        return False
