# Generated by Django 3.2.6 on 2023-07-05 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20220802_1216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='a2brelation',
            name='authority',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='a2brelation',
            name='confidence',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='a2brelation',
            name='end_date',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='a2brelation',
            name='start_date',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
