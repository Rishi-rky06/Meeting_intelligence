"""
APScheduler setup — starts a BackgroundScheduler for periodic reminder jobs.
"""

import logging
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = None


def start_scheduler():
    """
    Start the APScheduler background scheduler.
    Called from RemindersConfig.ready() to ensure it starts once per process.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler is already running — skipping re-start.")
        return

    interval_minutes = getattr(settings, 'SCHEDULER_INTERVAL_MINUTES', 30)

    _scheduler = BackgroundScheduler(timezone='UTC')
    _scheduler.add_job(
        _run_reminders,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='send_overdue_reminders',
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(f"Scheduler started — reminder job runs every {interval_minutes} minute(s).")


def _run_reminders():
    """Wrapper that imports and calls the job inside the Django app context."""
    try:
        from apps.reminders.jobs import send_overdue_reminders
        send_overdue_reminders()
    except Exception as exc:
        logger.exception(f"Reminder job failed: {exc}")


def get_scheduler() -> BackgroundScheduler:
    """Return the current scheduler instance (may be None if not started)."""
    return _scheduler
