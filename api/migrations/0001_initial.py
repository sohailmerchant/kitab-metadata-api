# Generated by Django 3.2.6 on 2022-07-27 15:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='a2bRelation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.CharField(blank=True, max_length=100)),
                ('end_date', models.CharField(blank=True, max_length=100)),
                ('authority', models.CharField(blank=True, max_length=100)),
                ('confidence', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='AggregatedStats',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('number_of_authors', models.IntegerField(null=True)),
                ('number_of_unique_authors', models.IntegerField(blank=True, null=True)),
                ('number_of_books', models.IntegerField(blank=True, null=True)),
                ('number_of_unique_books', models.IntegerField(blank=True, null=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('total_word_count', models.IntegerField(blank=True, null=True)),
                ('largest_book', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='authorMeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_uri', models.CharField(max_length=50, unique=True)),
                ('author_ar', models.CharField(blank=True, max_length=255)),
                ('author_lat', models.CharField(blank=True, max_length=255)),
                ('date', models.IntegerField(blank=True, null=True)),
                ('authorDateAH', models.IntegerField(blank=True, null=True)),
                ('authorDateCE', models.IntegerField(blank=True, null=True)),
                ('authorDateString', models.CharField(blank=True, max_length=255)),
                ('related_persons', models.ManyToManyField(through='api.a2bRelation', to='api.authorMeta')),
            ],
        ),
        migrations.CreateModel(
            name='placeMeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thuraya_uri', models.CharField(blank=True, max_length=100)),
                ('name_ar', models.CharField(blank=True, max_length=100)),
                ('name_lat', models.CharField(blank=True, max_length=100)),
                ('coordinates', models.CharField(blank=True, max_length=50)),
                ('place_relations', models.ManyToManyField(through='api.a2bRelation', to='api.placeMeta')),
            ],
        ),
        migrations.CreateModel(
            name='textMeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_uri', models.CharField(max_length=100, unique=True)),
                ('title_ar', models.CharField(blank=True, max_length=255)),
                ('title_lat', models.CharField(blank=True, max_length=255)),
                ('text_type', models.CharField(blank=True, max_length=10)),
                ('tags', models.CharField(blank=True, max_length=255)),
                ('author_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='texts', related_query_name='text', to='api.authormeta')),
                ('related_persons', models.ManyToManyField(through='api.a2bRelation', to='api.authorMeta')),
                ('related_places', models.ManyToManyField(through='api.a2bRelation', to='api.placeMeta')),
                ('related_texts', models.ManyToManyField(through='api.a2bRelation', to='api.textMeta')),
            ],
        ),
        migrations.CreateModel(
            name='versionMeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_id', models.CharField(max_length=50, unique=True)),
                ('version_uri', models.CharField(blank=True, max_length=100)),
                ('char_length', models.IntegerField(blank=True, null=True)),
                ('tok_length', models.IntegerField(blank=True, null=True)),
                ('url', models.CharField(blank=True, max_length=255)),
                ('editor', models.CharField(blank=True, max_length=100)),
                ('edition_place', models.CharField(blank=True, max_length=100)),
                ('publisher', models.CharField(blank=True, max_length=100)),
                ('edition_date', models.CharField(blank=True, max_length=100)),
                ('ed_info', models.CharField(blank=True, max_length=255)),
                ('version_lang', models.CharField(blank=True, max_length=3)),
                ('tags', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(blank=True, max_length=3)),
                ('annotation_status', models.CharField(blank=True, max_length=50)),
                ('text_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', related_query_name='version', to='api.textmeta')),
            ],
        ),
        migrations.CreateModel(
            name='relationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50)),
                ('name_inverted', models.CharField(blank=True, max_length=50)),
                ('descr', models.CharField(blank=True, max_length=255)),
                ('entities', models.CharField(blank=True, max_length=50)),
                ('parent_type', models.ManyToManyField(related_name='sub_types', related_query_name='sub_type', to='api.relationType')),
            ],
        ),
        migrations.CreateModel(
            name='personName',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=3, null=True)),
                ('shuhra', models.CharField(blank=True, max_length=255)),
                ('nasab', models.CharField(blank=True, max_length=255)),
                ('kunya', models.CharField(blank=True, max_length=255)),
                ('ism', models.CharField(blank=True, max_length=255)),
                ('laqab', models.CharField(blank=True, max_length=255)),
                ('nisba', models.CharField(blank=True, max_length=255)),
                ('author_id', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='personNames', related_query_name='personName', to='api.authormeta')),
            ],
        ),
        migrations.AddField(
            model_name='authormeta',
            name='related_places',
            field=models.ManyToManyField(through='api.a2bRelation', to='api.placeMeta'),
        ),
        migrations.AddField(
            model_name='a2brelation',
            name='person_a_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='related_persons_a', related_query_name='related_person_a', to='api.authormeta'),
        ),
        migrations.AddField(
            model_name='a2brelation',
            name='person_b_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='related_persons_b', related_query_name='related_person_b', to='api.authormeta'),
        ),
        migrations.AddField(
            model_name='a2brelation',
            name='place_a_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='related_places_a', related_query_name='related_place_a', to='api.placemeta'),
        ),
        migrations.AddField(
            model_name='a2brelation',
            name='place_b_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='related_places_b', related_query_name='related_place_b', to='api.placemeta'),
        ),
        migrations.AddField(
            model_name='a2brelation',
            name='relation_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='api.relationtype'),
        ),
        migrations.AddField(
            model_name='a2brelation',
            name='text_a_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='related_texts_a', related_query_name='related_text_a', to='api.textmeta'),
        ),
        migrations.AddField(
            model_name='a2brelation',
            name='text_b_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='related_texts_b', related_query_name='related_text_b', to='api.textmeta'),
        ),
    ]
