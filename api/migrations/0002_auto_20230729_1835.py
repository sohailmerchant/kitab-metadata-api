# Generated by Django 3.2.6 on 2023-07-29 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='versionmeta',
            name='tags',
        ),
        migrations.AddField(
            model_name='releasemeta',
            name='tags',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]