"""
Management command to check for stuck publishing workflows and fix them.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bubble.items.models import Item, ProcessingStatus


class Command(BaseCommand):
    help = "Check for stuck publishing workflows and fix them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--timeout-minutes",
            type=int,
            default=5,
            help="Consider workflows stuck after this many minutes (default: 5)",
        )

    def handle(self, *args, **options):
        timeout_minutes = options["timeout_minutes"]
        dry_run = options["dry_run"]

        # Find items stuck in processing state
        timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)

        stuck_items = Item.objects.filter(
            publishing_status=ProcessingStatus.PROCESSING,
            date_updated__lt=timeout_threshold,
        ).select_related("user")

        if not stuck_items.exists():
            self.stdout.write(
                self.style.SUCCESS("No stuck publishing workflows found.")
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Found {stuck_items.count()} items stuck in processing state "
                f"(older than {timeout_minutes} minutes):"
            )
        )

        for item in stuck_items:
            self.stdout.write(
                f'  - Item {item.id}: "{item.name}" by {item.user.username} '
                f"(workflow: {item.publishing_workflow_id})"
            )

            if not dry_run:
                # Check if embedding was actually generated
                if item.embedding is not None:
                    item.publishing_status = ProcessingStatus.COMPLETED
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    → Fixed: Item {item.id} had embedding, marked as COMPLETED"
                        )
                    )
                else:
                    item.publishing_status = ProcessingStatus.FAILED
                    self.stdout.write(
                        self.style.ERROR(
                            f"    → Fixed: Item {item.id} had no embedding, marked as FAILED"
                        )
                    )

                item.save(update_fields=["publishing_status"])

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis was a dry run. Use --no-dry-run to actually fix the items."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nFixed {stuck_items.count()} stuck publishing workflows."
                )
            )
