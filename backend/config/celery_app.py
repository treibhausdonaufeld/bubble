import os

from celery import Celery
from celery.signals import setup_logging

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("bubble")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Periodic tasks schedule
# Run bookings.check_bookings_active every 10 minutes to reconcile item statuses
app.conf.beat_schedule = app.conf.get("beat_schedule", {})
app.conf.beat_schedule.update(
    {
        "bookings.check_active_10min": {
            "task": "bubble.bookings.tasks.check_bookings_active",
            "schedule": 600.0,  # every 10 minutes
            "options": {"queue": "default"},
        }
    }
)


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig  # noqa: PLC0415

    from django.conf import settings  # noqa: PLC0415

    dictConfig(settings.LOGGING)


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
