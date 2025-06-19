#!/usr/bin/env python
"""
Fix migration dependency issue by directly manipulating the Django migrations table.
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import connection

def fix_migration_history():
    """Fix the migration history by marking tags.0001_initial as applied."""
    with connection.cursor() as cursor:
        # Insert the missing tags migration record
        # Use datetime.now() for compatibility with both SQLite and PostgreSQL
        from datetime import datetime
        
        try:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES (%s, %s, %s)
            """, ['tags', '0001_initial', datetime.now()])
            print("Fixed migration history: marked tags.0001_initial as applied")
        except Exception as e:
            print(f"Error inserting migration record: {e}")
            # Try with different parameter style for SQLite
            try:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES (?, ?, ?)
                """, ['tags', '0001_initial', datetime.now()])
                print("Fixed migration history: marked tags.0001_initial as applied (SQLite)")
            except Exception as e2:
                print(f"Failed with both parameter styles: {e2}")

if __name__ == '__main__':
    fix_migration_history()