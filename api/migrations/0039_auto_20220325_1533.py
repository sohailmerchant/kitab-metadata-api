# Generated by Django 3.2.6 on 2022-03-25 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0038_alter_versionmeta_textmeta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='versionmeta',
            name='releases',
        ),
        migrations.AddField(
            model_name='textmeta',
            name='text_type',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='versionmeta',
            name='status',
            field=models.CharField(blank=True, max_length=3),
        ),
    ]