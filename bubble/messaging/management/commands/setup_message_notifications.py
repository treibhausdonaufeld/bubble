import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Sets up periodic tasks for message notifications"

    def handle(self, *args, **options):
        # Create a crontab schedule for daily at 9 AM
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="9",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )

        # Create the periodic task for unread message notifications
        _task, created = PeriodicTask.objects.get_or_create(
            crontab=schedule,
            name="Send unread message notifications",
            task="bubble.messaging.tasks.send_unread_message_notifications",
            defaults={"enabled": True, "kwargs": json.dumps({})},
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully created periodic task "
                    "for unread message notifications"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Periodic task for unread message notifications already exists"
                )
            )

        # Create a crontab schedule for monthly cleanup (1st of each month at 3 AM)
        cleanup_schedule, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="3",
            day_of_week="*",
            day_of_month="1",
            month_of_year="*",
        )

        # Create the periodic task for message cleanup
        _cleanup_task, created = PeriodicTask.objects.get_or_create(
            crontab=cleanup_schedule,
            name="Cleanup old read messages",
            task="bubble.messaging.tasks.cleanup_old_read_messages",
            defaults={"enabled": True, "kwargs": json.dumps({})},
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully created periodic task for message cleanup"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("Periodic task for message cleanup already exists")
            )
