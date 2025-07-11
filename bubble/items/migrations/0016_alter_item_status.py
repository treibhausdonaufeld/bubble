# Generated by Django 5.2.3 on 2025-07-10 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0015_alter_item_item_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='status',
            field=models.IntegerField(choices=[(0, 'New'), (1, 'Used'), (2, 'Broken')], default=1, help_text='Condition of the item'),
        ),
    ]
