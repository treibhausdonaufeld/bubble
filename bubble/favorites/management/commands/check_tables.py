from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Check if favorite tables exist"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check what tables exist
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%favorite%'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()
            self.stdout.write("Favorite-related tables found:")
            for table in tables:
                self.stdout.write(f"  - {table[0]}")

            # Check the structure of the favorites table
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'favorites_favorite'
                ORDER BY ordinal_position;
            """)

            columns = cursor.fetchall()
            self.stdout.write("\nfavorites_favorite table structure:")
            for column in columns:
                self.stdout.write(
                    f"  - {column[0]} ({column[1]}) - Nullable: {column[2]}"
                )

            self.stdout.write(self.style.SUCCESS("Table check complete!"))
