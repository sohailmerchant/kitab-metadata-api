# Generated by Django 3.2.6 on 2022-03-25 09:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_rename_authormeta_authorname_author_uri'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorname',
            name='author_uri',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='authorMeta', to='api.authormeta'),
        ),
    ]
