# Generated by Django 3.2.6 on 2022-03-25 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_auto_20220325_0900'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authormeta',
            name='authorDateAH',
            field=models.IntegerField(max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='authormeta',
            name='authorDateCE',
            field=models.IntegerField(max_length=4, null=True),
        ),
    ]
