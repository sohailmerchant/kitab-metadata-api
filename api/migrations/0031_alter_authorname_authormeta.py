# Generated by Django 3.2.6 on 2022-03-25 10:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_rename_author_uri_authorname_authormeta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorname',
            name='authorMeta',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.authormeta'),
        ),
    ]