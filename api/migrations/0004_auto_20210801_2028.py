# Generated by Django 3.2.5 on 2021-08-01 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_book_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='char_length',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='tok_length',
            field=models.IntegerField(null=True),
        ),
    ]
