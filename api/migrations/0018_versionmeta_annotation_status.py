# Generated by Django 3.2.6 on 2022-03-25 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_auto_20220324_1909'),
    ]

    operations = [
        migrations.AddField(
            model_name='versionmeta',
            name='annotation_status',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
