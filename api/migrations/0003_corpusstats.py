# Generated by Django 3.2.6 on 2023-07-06 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20230706_0911'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorpusStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_1', models.CharField(max_length=50)),
                ('book_2', models.CharField(max_length=50)),
                ('instances_count', models.IntegerField(blank=True, null=True)),
                ('book1_word_match', models.IntegerField(blank=True, null=True)),
                ('book2_word_match', models.IntegerField(blank=True, null=True)),
            ],
        ),
    ]
