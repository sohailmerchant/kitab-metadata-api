# Generated by Django 3.2.6 on 2023-08-01 18:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_version_part_of'),
    ]

    operations = [
        migrations.AlterField(
            model_name='version',
            name='part_of',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='divisions', related_query_name='divided_into', to='api.version'),
        ),
    ]
