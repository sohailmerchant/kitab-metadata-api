# Generated by Django 3.2.6 on 2021-12-08 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_book_author_ar'),
    ]

    operations = [
        migrations.AddField(
            model_name='aggregatedstats',
            name='largest_book',
            field=models.IntegerField(null=True),
        ),
    ]
