# Generated by Django 5.2.3 on 2025-07-05 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0012_add_default_emojis'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemcategory',
            options={'ordering': ['ordering', 'name'], 'verbose_name_plural': 'Item Categories'},
        ),
        migrations.AddField(
            model_name='itemcategory',
            name='ordering',
            field=models.IntegerField(default=1, help_text='Order of display in navigation menu (lower numbers appear first)'),
        ),
    ]
