"""
Management command to manually trigger the overdue-reminder job.

Useful for testing the email integration without waiting for the
30-minute scheduler. Runs the exact same job the scheduler runs.

Usage:
    python manage.py send_reminders
"""

from django.core.management.base import BaseCommand
from apps.reminders.jobs import send_overdue_reminders


class Command(BaseCommand):
    help = 'Find overdue action items and send reminder emails immediately.'

    def handle(self, *args, **options):
        """Run the overdue reminder job once and report completion."""
        self.stdout.write('Running overdue reminder job...')
        send_overdue_reminders()
        self.stdout.write(self.style.SUCCESS(
            'Reminder job finished. Check your email and the ReminderLog table for results.'
        ))
