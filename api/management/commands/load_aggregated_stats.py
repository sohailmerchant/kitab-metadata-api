from django.db import models
from api.models import authorMeta, textMeta, versionMeta, personName, CorpusInsights
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models import Sum
from django.db.models import Max
import json
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, **options):
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            print(user, superusers)
        exit
        CorpusInsights.objects.all().delete()

        load_data()

# get the distinct count by providing a table name and a column


def get_distinct_count(table_name, column_name):
    distinct_count = table_name.objects.values(
        column_name).annotate(count=Count(column_name)).count()
    return distinct_count

# get a sum  by providing a table name and a column


def get_column_sum(table_name, column_name):
    column_sum = table_name.objects.aggregate(sum=Sum(column_name))['sum']
    return column_sum

# get largest number of book (word count) table name and a column or max of any column


def get_largest_number(table_name, column_name):
    largest_number = table_name.objects.aggregate(
        max_number=Max(column_name))['max_number']
    return largest_number


def get_top_10_books():

    # top_10_books = versionMeta.objects.select_related('text_id').order_by(
    #     '-tok_length')[:10].values('version_uri', 'tok_length', 'text_id__title_lat')

    #top_10_books = versionMeta.objects.order_by('-tok_length')[:10].values('version_uri', 'tok_length')
    all_books = versionMeta.objects.order_by(
        '-tok_length')[:60].values('version_uri', 'tok_length')

    top_books = dict()
    for b in all_books:
        text_uri = '.'.join(b['version_uri'].split('.')[:2])
        if text_uri not in top_books:
            top_books[text_uri] = b
        if len(top_books) == 10:
            break

    return top_books


# load data from the databse in aggregated format for the insight page
def load_data():
    # print(get_top_10_books())
    # print(textMeta.objects.annotate(Count('text_uri', distinct=True)).query)
    # print(versionMeta.objects.aggregate(sum=Sum('tok_length'))['sum'])

    CorpusInsights.objects.get_or_create(

        number_of_unique_authors=authorMeta.objects.count(),
        number_of_books=get_distinct_count(textMeta, 'text_uri'),
        number_of_versions=versionMeta.objects.count(),
        total_word_count=get_column_sum(versionMeta, 'tok_length'), # TO DO: moved to releaseMeta
        largest_book=get_largest_number(versionMeta, 'tok_length'),
        total_word_count_pri=versionMeta.objects.filter(status='pri').aggregate(sum=Sum('tok_length'))['sum'], # TO DO: moved to releaseMeta
        top_10_book_by_word_count=json.dumps(get_top_10_books())

    )
