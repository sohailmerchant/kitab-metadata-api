"""Load the aggregated corpus stats (number of authors/books/versions/...) into the database"""

from api.models import Author, Text, ReleaseVersion, CorpusInsights, ReleaseInfo
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Max
import json


class Command(BaseCommand):
    def handle(self, **options):
        #release_codes = ["2021.1.4", "2021.2.5", "2022.1.6", "2022.2.7"]
        #release_codes = ["2021.2.5", "2022.1.6", "2022.2.7", "post-release"]
        release_codes = ["2023.1.8"]
        for release_code in release_codes:
            print(release_code)
            load_aggregated_data(release_code)

def get_distinct_authors(release_code):
    return Author.objects\
            .filter(text__version__release_version__release_info__release_code=release_code)\
            .distinct().count()  # without distinct, it counts the number of rows in the join table!

def get_distinct_texts(release_code):
    return Text.objects\
            .filter(version__release_version__release_info__release_code=release_code)\
            .distinct().count()

def get_distinct_versions(release_code):
    return ReleaseVersion.objects.filter(release_info__release_code=release_code).count()

def get_distinct_primary_versions(release_code):
    return ReleaseVersion.objects.filter(release_info__release_code=release_code, analysis_priority="pri").count()

def get_distinct_secondary_versions(release_code):
    return ReleaseVersion.objects.filter(release_info__release_code=release_code, analysis_priority="sec").count()

def get_distinct_mARkdown_versions(release_code):
    return ReleaseVersion.objects.filter(release_info__release_code=release_code, annotation_status="mARkdown").count()

def get_distinct_completed_versions(release_code):
    return ReleaseVersion.objects.filter(release_info__release_code=release_code, annotation_status="completed").count()

def get_total_word_count(release_code):
    return ReleaseVersion.objects\
            .filter(release_info__release_code=release_code)\
            .aggregate(sum=Sum("tok_length"))['sum']

def get_total_word_count_pri(release_code):
    return ReleaseVersion.objects\
            .filter(release_info__release_code=release_code, analysis_priority="pri")\
            .aggregate(sum=Sum("tok_length"))['sum']

def get_largest_text(release_code):
    return ReleaseVersion.objects\
            .filter(release_info__release_code=release_code)\
            .aggregate(largest=Max("tok_length"))['largest']

def get_largest_books(release_code, n=10):
    all_books = ReleaseVersion.objects\
        .filter(release_info__release_code=release_code)\
        .values('version__version_uri', 'tok_length')\
        .order_by('-tok_length')

    top_books = dict()
    for b in all_books:
        text_uri = '.'.join(b['version__version_uri'].split('.')[:2])
        if text_uri not in top_books:
            top_books[text_uri] = b
        if len(top_books) == n:
            break

    return top_books


# # get the distinct count by providing a table name and a column

# def get_distinct_count(table_name, column_name):
#     distinct_count = table_name.objects.values(
#         column_name).annotate(count=Count(column_name)).count()
#     return distinct_count

# # get a sum  by providing a table name and a column


# def get_column_sum(table_name, column_name):
#     column_sum = table_name.objects.aggregate(sum=Sum(column_name))['sum']
#     return column_sum

# # get largest number of book (word count) table name and a column or max of any column


# def get_largest_number(table_name, column_name):
#     largest_number = table_name.objects.aggregate(
#         max_number=Max(column_name))['max_number']
#     return largest_number





def load_aggregated_data(release_code):
    """load data from the database in aggregated format for the insight page"""
    release_obj = ReleaseInfo.objects.get(release_code=release_code)

    # print(release_code)
    # print("get_distinct_authors:", get_distinct_authors(release_code))
    # print("get_distinct_texts:", get_distinct_texts(release_code))
    # print("get_distinct_versions:", get_distinct_versions(release_code))
    # print("get_total_word_count:", get_total_word_count(release_code))
    # print("get_largest_text:", get_largest_text(release_code))
    # print("get_total_word_count_pri:", get_total_word_count_pri(release_code))
    # print("json:", json.dumps(get_top_10_books(release_code), indent=2))
    # print("---------------------")

    CorpusInsights.objects.get_or_create(
        release_info=release_obj,
        number_of_authors=get_distinct_authors(release_code),
        number_of_books=get_distinct_texts(release_code),
        number_of_versions=get_distinct_versions(release_code),
        number_of_pri_versions=get_distinct_primary_versions(release_code),
        number_of_sec_versions=get_distinct_secondary_versions(release_code),
        number_of_markdown_versions=get_distinct_mARkdown_versions(release_code),
        number_of_completed_versions=get_distinct_completed_versions(release_code),
        total_word_count=get_total_word_count(release_code),
        total_word_count_pri=get_total_word_count_pri(release_code),
        largest_book=get_largest_text(release_code),
        largest_10_books=json.dumps(get_largest_books(release_code, 10))
    )

