# Generated by Django 5.2.3 on 2025-07-08 06:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_profile_address_alter_profile_bio_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="intern",
            new_name="internal",
        ),
    ]
