# Generated by Django 3.2.6 on 2023-07-27 06:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='textreusestats',
            name='release',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.DO_NOTHING, related_name='reuse_statistics', related_query_name='reuse_statistics', to='api.releasedetails'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='corpusinsights',
            name='release',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='corpus_statistics', related_query_name='corpus_statistics', to='api.releasedetails'),
        ),
    ]
