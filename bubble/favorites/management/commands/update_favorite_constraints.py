from django.core.management.base import BaseCommand
from django.db import DatabaseError, connection


class Command(BaseCommand):
    help = "Update unique constraints on favorites table"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write(
                "Updating unique constraints on favorites_favorite table..."
            )

            try:
                # Drop the old unique constraint
                cursor.execute("""
                    ALTER TABLE favorites_favorite
                    DROP CONSTRAINT IF EXISTS favorites_favorite_user_id_url_uniq;
                """)
                self.stdout.write("Dropped old unique constraint")

                # Add new unique constraint including favorite_list_id
                cursor.execute("""
                    ALTER TABLE favorites_favorite
                    ADD CONSTRAINT favorites_favorite_user_id_url_favorite_list_id_uniq
                    UNIQUE (user_id, url, favorite_list_id);
                """)
                self.stdout.write("Added new unique constraint with favorite_list_id")

            except DatabaseError as e:
                self.stdout.write(f"Error updating constraints: {e}")

            self.stdout.write(
                self.style.SUCCESS("Successfully updated favorite constraints!")
            )
