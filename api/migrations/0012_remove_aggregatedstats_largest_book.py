# Generated by Django 3.2.6 on 2021-12-08 00:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_aggregatedstats_largest_book'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aggregatedstats',
            name='largest_book',
        ),
    ]