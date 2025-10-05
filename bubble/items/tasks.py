"""Celery tasks for the items app."""

from celery import shared_task
from django.core.management import call_command


@shared_task
def cleanup_old_searches():
    """Clean up old similarity searches."""
    call_command("cleanup_searches", days=7)
