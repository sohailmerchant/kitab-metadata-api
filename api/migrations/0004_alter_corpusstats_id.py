# Generated by Django 3.2.6 on 2023-07-06 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_corpusstats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpusstats',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
