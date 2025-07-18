# Generated by Django 5.2.3 on 2025-07-14 18:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0018_remove_item_profile_img_frame_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ItemCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("emoji", models.CharField(blank=True, max_length=10)),
                (
                    "ordering",
                    models.IntegerField(
                        default=1,
                        help_text="Order of display in navigation menu (lower numbers appear first)",
                    ),
                ),
                (
                    "parent_category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subcategories",
                        to="items.itemcategory",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Item Categories",
                "ordering": ["ordering", "name"],
            },
        ),
        migrations.AddField(
            model_name="item",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="items",
                to="items.itemcategory",
            ),
        ),
    ]
