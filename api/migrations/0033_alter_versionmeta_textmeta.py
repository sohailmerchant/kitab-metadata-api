# Generated by Django 3.2.6 on 2022-03-25 11:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0032_alter_textmeta_authormeta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='versionmeta',
            name='textMeta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versons', to='api.textmeta'),
        ),
    ]