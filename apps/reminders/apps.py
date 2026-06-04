"""
Reminders app config — starts the APScheduler background job on server startup.
"""

import logging
import os
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class RemindersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reminders'
    label = 'reminders'

    def ready(self):
        """
        Start the scheduler when Django finishes loading.
        The RUN_MAIN guard prevents double-start in Django's development
        auto-reloader (which spawns a subprocess).
        """
        if os.environ.get('RUN_MAIN') != 'true' and os.environ.get('DISABLE_SCHEDULER') != 'true':
            from apps.reminders.scheduler import start_scheduler
            start_scheduler()
