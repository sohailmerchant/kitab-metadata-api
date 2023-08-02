from django_filters import rest_framework as django_filters
from rest_framework import filters

from .models import Author, PersonName, Text, Version, CorpusInsights, ReleaseVersion, TextReuseStats


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    """
    Create a filter that allows comma-separated numbers in API call
    https://django-filter.readthedocs.io/en/latest/ref/filters.html#baseinfilter
    """
    pass  # no need to do anything more than this!


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """
    Create a filter that allows comma-separated strings in API call
    https://django-filter.readthedocs.io/en/latest/ref/filters.html#baseinfilter
    """
    pass  # no need to do anything more than this!


class NumberRangeFilter(django_filters.BaseRangeFilter, django_filters.NumberFilter):
    """
    Create a filter that allows comma-separated range in API call
    https://django-filter.readthedocs.io/en/latest/ref/filters.html#baserangefilter
    """
    pass  # no need to do anything more than this!


class AuthorFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for authors

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/author/all/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/author/all/?text_title_ar=تاريخ
    http://127.0.0.1:8000/author/all/?date_AH=310
    http://127.0.0.1:8000/author/all/?author_uri=0310Tabari

    """
    #author_ar_contains = django_filters.CharFilter(field_name="author_ar", lookup_expr='icontains')
    #author_lat_contains = django_filters.CharFilter(field_name="author_lat", lookup_expr='icontains')
    author_ar = django_filters.CharFilter(
        field_name="author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="author_lat", lookup_expr='icontains')
    died_after_AH = django_filters.NumberFilter(
        field_name="date_AH", lookup_expr="gt")  # /?died_after_AH=309
    died_before_AH = django_filters.NumberFilter(
        field_name="date_AH", lookup_expr="lt")  # /?died_before_AH=311
    died_between_AH = NumberRangeFilter(
        field_name="date_AH", lookup_expr="range")       # /?died_between_AH=309,311

    shuhra = django_filters.CharFilter(
        field_name="name_element__shuhra", lookup_expr='icontains')
    ism = django_filters.CharFilter(
        field_name="name_element__ism", lookup_expr='icontains')
    nasab = django_filters.CharFilter(
        field_name="name_element__nasab", lookup_expr='icontains')
    kunya = django_filters.CharFilter(
        field_name="name_element__kunya", lookup_expr='icontains')
    laqab = django_filters.CharFilter(
        field_name="name_element__laqab", lookup_expr='icontains')
    nisba = django_filters.CharFilter(
        field_name="name_element__nisba", lookup_expr='icontains')

    text_title_ar = django_filters.CharFilter(
        field_name="text__titles_ar", lookup_expr='icontains')
    text_title_lat = django_filters.CharFilter(
        field_name="text__titles_lat", lookup_expr='icontains')

    class Meta:
        model = Author
        # additional fields with the default lookup ("exact"):
        #fields = ["author_uri", "author_lat", "author_ar", "date_AH"]
        fields = ["author_uri", "date_AH", "id"]


class VersionFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for versions

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/version/all/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/version/all/?title_ar=تاريخ
    http://127.0.0.1:8000/version/all/?date_AH=310
    http://127.0.0.1:8000/version/all/?author_uri=0310Tabari

    """
    version_uri_contains = django_filters.CharFilter(
        field_name="version_uri", lookup_expr='icontains')  # "exact" is default
    char_count_lte = django_filters.NumberFilter(
        field_name="release_version__char_length", lookup_expr="lte")
    char_count_gte = django_filters.NumberFilter(
        field_name="release_version__char_length", lookup_expr="gte")
    tok_count_lte = django_filters.NumberFilter(
        field_name="release_version__tok_length", lookup_expr="lte")
    tok_count_gte = django_filters.NumberFilter(
        field_name="release_version__tok_length", lookup_expr="gte")
    tags = django_filters.CharFilter(
        field_name="release_version__tags", lookup_expr='icontains')  # /?tags=_SHICR
    editor = django_filters.CharFilter(
        field_name="edition__editor", lookup_expr='icontains')
    edition_place = django_filters.CharFilter(
        field_name="edition__edition_place", lookup_expr='icontains')
    publisher = django_filters.CharFilter(
        field_name="edition__publisher", lookup_expr='icontains')
    edition_date = django_filters.CharFilter(
        field_name="edition__edition_date", lookup_expr='icontains')
    edition = django_filters.CharFilter(
        field_name="edition__ed_info", lookup_expr='icontains')
    # this field is currently always null
    language = CharInFilter(field_name="language", lookup_expr='in')
    analysis_priority = CharInFilter(field_name="release_version__analysis_priority", lookup_expr='in')
    annotation_status = CharInFilter(field_name="release_version__annotation_status", lookup_expr='in')
    title_ar = django_filters.CharFilter(
        field_name="text__titles_ar", lookup_expr='icontains')
    title_lat = django_filters.CharFilter(
        field_name="text__titles_lat", lookup_expr='icontains')
    
    author_ar = django_filters.CharFilter(
        field_name="text__author__author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="text__author__author_lat", lookup_expr='icontains')
    died_after_AH = django_filters.NumberFilter(
        field_name="text__author__date_AH", lookup_expr="gt")
    died_before_AH = django_filters.NumberFilter(
        field_name="text__author__date_AH", lookup_expr="lt")
    died_between_AH = NumberRangeFilter(
        field_name="text__author__date_AH", lookup_expr="range")  # /?died_between_AH=309,311
    shuhra = django_filters.CharFilter(
        field_name="text__author__name_element__shuhra", lookup_expr='icontains')
    ism = django_filters.CharFilter(
        field_name="text__author__name_element__ism", lookup_expr='icontains')
    nasab = django_filters.CharFilter(
        field_name="text__author__name_element__nasab", lookup_expr='icontains')
    kunya = django_filters.CharFilter(
        field_name="text__author__name_element__kunya", lookup_expr='icontains')
    laqab = django_filters.CharFilter(
        field_name="text__author__name_element__laqab", lookup_expr='icontains')
    nisba = django_filters.CharFilter(
        field_name="text__author__name_element__nisba", lookup_expr='icontains')

    class Meta:
        model = Version
        # additional fields with the default lookup ("exact"):
        fields = ["version_uri", "id"]


class TextFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for texts

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/text/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/author/?text_title_ar=تاريخ
    http://127.0.0.1:8000/author/?date_AH=310
    http://127.0.0.1:8000/author/?author_uri=0310Tabari

    """
    #author_ar_contains = django_filters.CharFilter(field_name="author_ar", lookup_expr='icontains')
    #author_lat_contains = django_filters.CharFilter(field_name="author_lat", lookup_expr='icontains')
    title_ar = django_filters.CharFilter(
        field_name="text__titles_ar", lookup_expr='icontains')
    title_lat = django_filters.CharFilter(
        field_name="text__titles_lat", lookup_expr='icontains')
    text_type = django_filters.CharFilter(
        field_name="text_type", lookup_expr='icontains')
    tag = django_filters.CharFilter(field_name="tags", lookup_expr='icontains')

    author_ar = django_filters.CharFilter(
        field_name="author__author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="author__author_lat", lookup_expr='icontains')
    author_died_after_AH = django_filters.NumberFilter(
        field_name="author__date_AH", lookup_expr="gt")  # /?died_after_AH=309
    author_died_before_AH = django_filters.NumberFilter(
        field_name="author__date_AH", lookup_expr="lt")  # /?died_before_AH=311
    author_died_between_AH = NumberRangeFilter(
        field_name="author__date_AH", lookup_expr="range")       # /?died_between_AH=309,311

    author_shuhra = django_filters.CharFilter(
        field_name="author__name_element__shuhra", lookup_expr='icontains')
    author_ism = django_filters.CharFilter(
        field_name="author__name_element__ism", lookup_expr='icontains')
    author_nasab = django_filters.CharFilter(
        field_name="author__name_element__nasab", lookup_expr='icontains')
    author_kunya = django_filters.CharFilter(
        field_name="author__name_element__kunya", lookup_expr='icontains')
    author_laqab = django_filters.CharFilter(
        field_name="author__name_element__laqab", lookup_expr='icontains')
    author_nisba = django_filters.CharFilter(
        field_name="author__name_element__nisba", lookup_expr='icontains')

    related_text_title_lat = django_filters.CharFilter(
        field_name="related_texts__titles_lat", lookup_expr='icontains')

    class Meta:
        model = Text
        # additional fields with the default lookup ("exact"):
        #fields = ["author_uri", "author_lat", "author_ar", "date_AH"]
        fields = ["text_uri", "id"]


class TextReuseFilter(django_filters.FilterSet):
    """Filters for views based on the TextReuseStats model"""
    # filter on version URI: 
    book_1 = django_filters.CharFilter(
        field_name="book_1__version__version_uri", lookup_expr='icontains')
    book_2 = django_filters.CharFilter(
        field_name="book_2__version__version_uri", lookup_expr='icontains')
    
    # filter on the number of text reuse instances:
    instances_count_gt = django_filters.NumberFilter(
        field_name="instances_count", lookup_expr="gt")
    instances_count_lt = django_filters.NumberFilter(
        field_name="instances_count", lookup_expr="lt")
    instances_count_range = django_filters.NumericRangeFilter(
        field_name="instances_count", lookup_expr="range")
    # NB: example of the range filter in url query string: 
    # ?instances_count_range_min=10&instances_count_range_max=80

    # filter on the number of words in book 1 that are matched in book 2:
    book1_words_matched_gt = django_filters.NumberFilter(
        field_name="book1_words_matched", lookup_expr="gt")
    book1_words_matched_lt = django_filters.NumberFilter(
        field_name="book1_words_matched", lookup_expr="lt")
    book1_words_matched_range = django_filters.NumericRangeFilter(
        field_name="book1_words_matched", lookup_expr="range")

    # filter on the number of words in book 2 that are matched in book 1:
    book2_words_matched_gt = django_filters.NumberFilter(
        field_name="book2_words_matched", lookup_expr="gt")
    book2_words_matched_lt = django_filters.NumberFilter(
        field_name="book2_words_matched", lookup_expr="lt")
    book2_words_matched_range = django_filters.NumericRangeFilter(
        field_name="book2_words_matched", lookup_expr="range")

    # filter on the percentage of words in book 1 that are matched in book 2:
    book1_pct_words_matched_gt = django_filters.NumberFilter(
        field_name="book1_pct_words_matched", lookup_expr="gt")
    book1_pct_words_matched_lt = django_filters.NumberFilter(
        field_name="book1_pct_words_matched", lookup_expr="lt")
    book1_pct_words_matched_range = django_filters.NumericRangeFilter(
        field_name="book1_pct_words_matched", lookup_expr="range")

    # filter on the percentage of words in book 2 that are matched in book 1:
    book2_pct_words_matched_gt = django_filters.NumberFilter(
        field_name="book2_pct_words_matched", lookup_expr="gt")
    book2_pct_words_matched_lt = django_filters.NumberFilter(
        field_name="book2_pct_words_matched", lookup_expr="lt")
    book2_pct_words_matched_range = django_filters.NumericRangeFilter(
        field_name="book2_pct_words_matched", lookup_expr="range")

    class Meta:
        model = TextReuseStats
        # additional fields with the default lookup ("exact"):
        fields = []

class ReleaseVersionFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for versions

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/version/all/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/version/all/?book_title_ar=تاريخ
    http://127.0.0.1:8000/version/all/?date_AH=310
    http://127.0.0.1:8000/version/all/?author_uri=0310Tabari

    """
    release_code_contains = django_filters.CharFilter(
        field_name="release_info__release_code", lookup_expr='icontains')
    release_code = django_filters.CharFilter(
        field_name="release_info__release_code", lookup_expr='exact')
    
    version_uri_contains = django_filters.CharFilter(
        field_name="version__version_uri", lookup_expr='icontains')  # "exact" is default
    char_count_lte = django_filters.NumberFilter(
        field_name="char_length", lookup_expr="lte")
    char_count_gte = django_filters.NumberFilter(
        field_name="char_length", lookup_expr="gte")
    tok_count_lte = django_filters.NumberFilter(
        field_name="tok_length", lookup_expr="lte")
    tok_count_gte = django_filters.NumberFilter(
        field_name="tok_length", lookup_expr="gte")

    editor = django_filters.CharFilter(
        field_name="version__edition__editor", lookup_expr='icontains')
    edition_place = django_filters.CharFilter(
        field_name="version__edition__edition_place", lookup_expr='icontains')
    publisher = django_filters.CharFilter(
        field_name="version__edition__publisher", lookup_expr='icontains')
    edition_date = django_filters.CharFilter(
        field_name="version__edition__edition_date", lookup_expr='icontains')
    edition = django_filters.CharFilter(
        field_name="version__edition__ed_info", lookup_expr='icontains')
    # this field is currently always null
    language = CharInFilter(
        field_name="version__language", lookup_expr='in')
    tags = django_filters.CharFilter(
        field_name="version__release_version__tags", lookup_expr='icontains')  # /?tags=_SHICR
    analysis_priority = CharInFilter(
        field_name="analysis_priority", lookup_expr='in')
    annotation_status = CharInFilter(
        field_name="annotation_status", lookup_expr='in')

    title_ar = django_filters.CharFilter(
        field_name="version__text__titles_ar", lookup_expr='icontains')
    title_lat = django_filters.CharFilter(
        field_name="version__text__titles_lat", lookup_expr='icontains')    
    author_ar = django_filters.CharFilter(
        field_name="version__text__author__author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="version__text__author__author_lat", lookup_expr='icontains')
    died_after_AH = django_filters.NumberFilter(
        field_name="version__text__author__date_AH", lookup_expr="gt")
    died_before_AH = django_filters.NumberFilter(
        field_name="version__text__author__date_AH", lookup_expr="lt")
    died_between_AH = NumberRangeFilter(
        field_name="version__text__author__date_AH", lookup_expr="range")  # /?died_between_AH=309,311
    shuhra = django_filters.CharFilter(
        field_name="version__text__author__name_element__shuhra", lookup_expr='icontains')
    ism = django_filters.CharFilter(
        field_name="version__text__author__name_element__ism", lookup_expr='icontains')
    nasab = django_filters.CharFilter(
        field_name="version__text__author__name_element__nasab", lookup_expr='icontains')
    kunya = django_filters.CharFilter(
        field_name="version__text__author__name_element__kunya", lookup_expr='icontains')
    laqab = django_filters.CharFilter(
        field_name="version__text__author__name_element__laqab", lookup_expr='icontains')
    nisba = django_filters.CharFilter(
        field_name="version__text__author__name_element__nisba", lookup_expr='icontains')

    class Meta:
        model = ReleaseVersion
        # additional fields with the default lookup ("exact"):
        fields = ["release_info__release_code", "id", "version__version_uri"]
