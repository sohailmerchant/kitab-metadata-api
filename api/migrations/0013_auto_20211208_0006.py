# Generated by Django 3.2.6 on 2021-12-08 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_remove_aggregatedstats_largest_book'),
    ]

    operations = [
        migrations.AddField(
            model_name='aggregatedstats',
            name='largest_book',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='aggregatedstats',
            name='total_word_count',
            field=models.IntegerField(null=True),
        ),
    ]
