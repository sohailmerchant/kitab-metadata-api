# Generated by Django 3.2.6 on 2022-03-24 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_auto_20220324_1805'),
    ]

    operations = [
        migrations.RenameField(
            model_name='textrelations',
            old_name='verion1_Id',
            new_name='Id1',
        ),
        migrations.RenameField(
            model_name='textrelations',
            old_name='verion2_Id',
            new_name='Id2',
        ),
        migrations.RemoveField(
            model_name='textrelations',
            name='textRelationID',
        ),
        migrations.AlterField(
            model_name='versionmeta',
            name='version_id',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
