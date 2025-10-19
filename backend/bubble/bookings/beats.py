from celery.schedules import crontab

from config.celery_app import app

# Periodic tasks schedule
app.conf.beat_schedule = app.conf.get("beat_schedule", {})
app.conf.beat_schedule.update(
    {
        "bookings.check_active_10min": {
            "task": "bubble.bookings.tasks.check_bookings_active",
            "schedule": crontab(minute="*/1"),
        }
    }
)
