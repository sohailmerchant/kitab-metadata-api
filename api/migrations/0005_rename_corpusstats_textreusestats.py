# Generated by Django 3.2.6 on 2023-07-06 14:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_corpusstats_id'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CorpusStats',
            new_name='TextReuseStats',
        ),
    ]
