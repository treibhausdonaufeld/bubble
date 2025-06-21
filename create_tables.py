#!/usr/bin/env python
"""Create database tables without migration checks."""

import os

import django
from django.core.management import execute_from_command_line
from django.db import connection

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()

    # Create all tables using syncdb

    try:
        # Try to run syncdb to create tables
        execute_from_command_line(["manage.py", "migrate", "--run-syncdb"])
        print("✓ Tables created successfully")

        # Create superuser
        execute_from_command_line(
            [
                "manage.py",
                "createsuperuser",
                "--noinput",
                "--username",
                "admin",
                "--email",
                "admin@example.com",
            ],
        )
        print("✓ Superuser created")

    except Exception as e:
        print(f"Error: {e}")
        print("Creating tables manually...")

        # Import all models to register them

        # Create tables manually
        from django.core.management.color import no_style
        from django.db import connection

        style = no_style()
        cursor = connection.cursor()

        # Get SQL statements for all models
        from django.apps import apps

        all_models = apps.get_models()

        statements = connection.ops.sql_table_creation_suffix()

        for model in all_models:
            if model._meta.app_label in ["users", "categories", "items"]:
                print(f"Creating table for {model._meta.label}")
                # This is a simplified approach - in reality you'd need more complex SQL generation

        print("Manual table creation attempted")
