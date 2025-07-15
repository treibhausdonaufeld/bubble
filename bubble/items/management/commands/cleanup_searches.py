"""Management command to clean up old similarity searches."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bubble.items.models import SearchStatus, SimilaritySearch


class Command(BaseCommand):
    help = "Clean up old similarity searches from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to keep completed searches (default: 7)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        days_to_keep = options["days"]
        dry_run = options["dry_run"]

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Find old completed and failed searches
        old_searches = SimilaritySearch.objects.filter(
            status__in=[SearchStatus.COMPLETED, SearchStatus.FAILED],
            date_completed__lt=cutoff_date,
        )

        # Also find very old pending/processing searches (likely stuck)
        very_old_cutoff = timezone.now() - timedelta(days=1)  # 1 day old
        stuck_searches = SimilaritySearch.objects.filter(
            status__in=[SearchStatus.PENDING, SearchStatus.PROCESSING],
            date_created__lt=very_old_cutoff,
        )

        total_old = old_searches.count()
        total_stuck = stuck_searches.count()
        total_to_delete = total_old + total_stuck

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {total_old} old searches "
                    f"(completed/failed older than {days_to_keep} days)"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {total_stuck} stuck searches "
                    f"(pending/processing older than 1 day)"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Total searches to delete: {total_to_delete}"
                )
            )

            if total_to_delete > 0:
                self.stdout.write("Preview of searches to be deleted:")
                for search in old_searches[:5]:  # Show first 5
                    self.stdout.write(f"  - {search.search_id}: {search.query[:50]}...")
                if total_old > 5:
                    self.stdout.write(f"  ... and {total_old - 5} more old searches")

                for search in stuck_searches[:5]:  # Show first 5 stuck
                    self.stdout.write(
                        f"  - {search.search_id}: {search.query[:50]}... (STUCK)"
                    )
                if total_stuck > 5:
                    self.stdout.write(
                        f"  ... and {total_stuck - 5} more stuck searches"
                    )

        else:
            if total_to_delete == 0:
                self.stdout.write(
                    self.style.SUCCESS("No old searches found to clean up.")
                )
                return

            # Delete old completed/failed searches
            deleted_old, _ = old_searches.delete()

            # Delete stuck searches
            deleted_stuck, _ = stuck_searches.delete()

            total_deleted = deleted_old + deleted_stuck

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleaned up {deleted_old} old searches "
                    f"(completed/failed older than {days_to_keep} days)"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleaned up {deleted_stuck} stuck searches "
                    f"(pending/processing older than 1 day)"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f"Total searches deleted: {total_deleted}")
            )
