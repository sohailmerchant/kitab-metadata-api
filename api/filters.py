from django_filters import rest_framework as django_filters
from rest_framework import filters

from .models import authorMeta, personName, textMeta, versionMeta, CorpusInsights, ReleaseMeta


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


class authorFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for authors

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/author/all/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/author/all/?text_title_ar=تاريخ
    http://127.0.0.1:8000/author/all/?authorDateAH=310
    http://127.0.0.1:8000/author/all/?author_uri=0310Tabari

    """
    #author_ar_contains = django_filters.CharFilter(field_name="author_ar", lookup_expr='icontains')
    #author_lat_contains = django_filters.CharFilter(field_name="author_lat", lookup_expr='icontains')
    author_ar = django_filters.CharFilter(
        field_name="author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="author_lat", lookup_expr='icontains')
    died_after_AH = django_filters.NumberFilter(
        field_name="authorDateAH", lookup_expr="gt")  # /?died_after_AH=309
    died_before_AH = django_filters.NumberFilter(
        field_name="authorDateAH", lookup_expr="lt")  # /?died_before_AH=311
    died_between_AH = NumberRangeFilter(
        field_name="authorDateAH", lookup_expr="range")       # /?died_between_AH=309,311

    shuhra = django_filters.CharFilter(
        field_name="personName__shuhra", lookup_expr='icontains')
    ism = django_filters.CharFilter(
        field_name="personName__ism", lookup_expr='icontains')
    nasab = django_filters.CharFilter(
        field_name="personName__nasab", lookup_expr='icontains')
    kunya = django_filters.CharFilter(
        field_name="personName__kunya", lookup_expr='icontains')
    laqab = django_filters.CharFilter(
        field_name="personName__laqab", lookup_expr='icontains')
    nisba = django_filters.CharFilter(
        field_name="personName__nisba", lookup_expr='icontains')

    text_title_ar = django_filters.CharFilter(
        field_name="text__title_ar", lookup_expr='icontains')
    text_title_lat = django_filters.CharFilter(
        field_name="text__title_lat", lookup_expr='icontains')

    class Meta:
        model = authorMeta
        # additional fields with the default lookup ("exact"):
        #fields = ["author_uri", "author_lat", "author_ar", "authorDateAH"]
        fields = ["author_uri", "authorDateAH", "id"]


class versionFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for versions

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/version/all/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/version/all/?book_title_ar=تاريخ
    http://127.0.0.1:8000/version/all/?authorDateAH=310
    http://127.0.0.1:8000/version/all/?author_uri=0310Tabari

    """
    version_uri_contains = django_filters.CharFilter(
        field_name="version_uri", lookup_expr='icontains')  # "exact" is default
    char_count_lte = django_filters.NumberFilter(
        field_name="char_length", lookup_expr="lte")
    char_count_gte = django_filters.NumberFilter(
        field_name="char_length", lookup_expr="gte")
    tok_count_lte = django_filters.NumberFilter(
        field_name="tok_length", lookup_expr="lte")
    tok_count_gte = django_filters.NumberFilter(
        field_name="tok_length", lookup_expr="gte")
    editor = django_filters.CharFilter(
        field_name="editor", lookup_expr='icontains')
    editor_place = django_filters.CharFilter(
        field_name="editor_place", lookup_expr='icontains')
    publisher = django_filters.CharFilter(
        field_name="publisher", lookup_expr='icontains')
    edition_date = django_filters.CharFilter(
        field_name="edition_date", lookup_expr='icontains')
    edition = django_filters.CharFilter(
        field_name="ed_info", lookup_expr='icontains')
    # this field is currently always null
    language = CharInFilter(field_name="version_lang", lookup_expr='in')
    tags = django_filters.CharFilter(
        field_name="tags", lookup_expr='icontains')  # /?tags=_SHICR
    status = CharInFilter(field_name="status", lookup_expr='in')
    annotation_status = CharInFilter(
        field_name="annotation_status", lookup_expr='in')

    title_ar = django_filters.CharFilter(
        field_name="text_id__title_ar", lookup_expr='icontains')
    title_lat = django_filters.CharFilter(
        field_name="text_id__title_lat", lookup_expr='icontains')
    
    author_ar = django_filters.CharFilter(
        field_name="text_id__author_id__author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="text_id__author_id__author_lat", lookup_expr='icontains')
    died_after_AH = django_filters.NumberFilter(
        field_name="text_id__author_id__authorDateAH", lookup_expr="gt")
    died_before_AH = django_filters.NumberFilter(
        field_name="text_id__author_id__authorDateAH", lookup_expr="lt")
    died_between_AH = NumberRangeFilter(
        field_name="text_id__author_id__authorDateAH", lookup_expr="range")  # /?died_between_AH=309,311
    shuhra = django_filters.CharFilter(
        field_name="text_id__author_id__personName__shuhra", lookup_expr='icontains')
    ism = django_filters.CharFilter(
        field_name="text_id__author_id__personName__ism", lookup_expr='icontains')
    nasab = django_filters.CharFilter(
        field_name="text_id__author_id__personName__nasab", lookup_expr='icontains')
    kunya = django_filters.CharFilter(
        field_name="text_id__author_id__personName__kunya", lookup_expr='icontains')
    laqab = django_filters.CharFilter(
        field_name="text_id__author_id__personName__laqab", lookup_expr='icontains')
    nisba = django_filters.CharFilter(
        field_name="text_id__author_id__personName__nisba", lookup_expr='icontains')

    class Meta:
        model = versionMeta
        # additional fields with the default lookup ("exact"):
        fields = ["version_uri", "id"]


class textFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for texts

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/text/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/author/?text_title_ar=تاريخ
    http://127.0.0.1:8000/author/?authorDateAH=310
    http://127.0.0.1:8000/author/?author_uri=0310Tabari

    """
    #author_ar_contains = django_filters.CharFilter(field_name="author_ar", lookup_expr='icontains')
    #author_lat_contains = django_filters.CharFilter(field_name="author_lat", lookup_expr='icontains')
    title_ar = django_filters.CharFilter(
        field_name="text_id__title_ar", lookup_expr='icontains')
    title_lat = django_filters.CharFilter(
        field_name="text_id__title_lat", lookup_expr='icontains')
    text_type = django_filters.CharFilter(
        field_name="text_type", lookup_expr='icontains')
    tag = django_filters.CharFilter(field_name="tags", lookup_expr='icontains')

    author_ar = django_filters.CharFilter(
        field_name="author_id__author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="author_id__author_lat", lookup_expr='icontains')
    author_died_after_AH = django_filters.NumberFilter(
        field_name="author_id__authorDateAH", lookup_expr="gt")  # /?died_after_AH=309
    author_died_before_AH = django_filters.NumberFilter(
        field_name="author_id__authorDateAH", lookup_expr="lt")  # /?died_before_AH=311
    author_died_between_AH = NumberRangeFilter(
        field_name="author_id__authorDateAH", lookup_expr="range")       # /?died_between_AH=309,311

    author_shuhra = django_filters.CharFilter(
        field_name="author_id__personName__shuhra", lookup_expr='icontains')
    author_ism = django_filters.CharFilter(
        field_name="author_id__personName__ism", lookup_expr='icontains')
    author_nasab = django_filters.CharFilter(
        field_name="author_id__personName__nasab", lookup_expr='icontains')
    author_kunya = django_filters.CharFilter(
        field_name="author_id__personName__kunya", lookup_expr='icontains')
    author_laqab = django_filters.CharFilter(
        field_name="author_id__personName__laqab", lookup_expr='icontains')
    author_nisba = django_filters.CharFilter(
        field_name="author_id__personName__nisba", lookup_expr='icontains')

    related_text_title_lat = django_filters.CharFilter(
        field_name="related_texts__title_lat", lookup_expr='icontains')

    class Meta:
        model = textMeta
        # additional fields with the default lookup ("exact"):
        #fields = ["author_uri", "author_lat", "author_ar", "authorDateAH"]
        fields = ["text_uri", "id"]


class textReuseFilter(django_filters.FilterSet):
    book_1 = django_filters.CharFilter(
        field_name="book_1__version_id", lookup_expr='icontains')
    book_2 = django_filters.CharFilter(
        field_name="book_2__version_id", lookup_expr='icontains')
    
    instances_count_gt = django_filters.NumberFilter(
        field_name="instances_count", lookup_expr="gt")
    instances_count_lt = django_filters.NumberFilter(
        field_name="instances_count", lookup_expr="lt")
    instances_count_range = django_filters.NumberFilter(
        field_name="instances_count", lookup_expr="range")

    book1_word_match_gt = django_filters.NumberFilter(
        field_name="book1_word_match", lookup_expr="gt")
    book1_word_match_lt = django_filters.NumberFilter(
        field_name="book1_word_match", lookup_expr="lt")
    book1_word_match_range = django_filters.NumberFilter(
        field_name="book1_word_match", lookup_expr="range")

    book2_word_match_gt = django_filters.NumberFilter(
        field_name="book2_word_match", lookup_expr="gt")
    book2_word_match_lt = django_filters.NumberFilter(
        field_name="book2_word_match", lookup_expr="lt")
    book2_word_match_range = django_filters.NumberFilter(
        field_name="book2_word_match", lookup_expr="range")

    book1_match_book2_per_per_gt = django_filters.NumberFilter(
        field_name="book1_match_book2_per", lookup_expr="gt")
    book1_match_book2_per_per_lt = django_filters.NumberFilter(
        field_name="book1_match_book2_per", lookup_expr="lt")
    book1_match_book2_per_per_range = django_filters.NumberFilter(
        field_name="book1_match_book2_per", lookup_expr="range")

    book2_match_book1_per_gt = django_filters.NumberFilter(
        field_name="book2_match_book1_per", lookup_expr="gt")
    book2_match_book1_per_lt = django_filters.NumberFilter(
        field_name="book2_match_book1_per", lookup_expr="lt")
    book2_match_book1_per_range = django_filters.NumberFilter(
        field_name="book2_match_book1_per", lookup_expr="range")


class releaseFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for versions

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/version/all/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/version/all/?book_title_ar=تاريخ
    http://127.0.0.1:8000/version/all/?authorDateAH=310
    http://127.0.0.1:8000/version/all/?author_uri=0310Tabari

    """
    release_code_contains = django_filters.CharFilter(
        field_name="release_code", lookup_expr='icontains')

    version_uri_contains = django_filters.CharFilter(
        field_name="version_uri__version_uri", lookup_expr='icontains')  # "exact" is default
    char_count_lte = django_filters.NumberFilter(
        field_name="char_length", lookup_expr="lte")
    char_count_gte = django_filters.NumberFilter(
        field_name="char_length", lookup_expr="gte")
    tok_count_lte = django_filters.NumberFilter(
        field_name="tok_length", lookup_expr="lte")
    tok_count_gte = django_filters.NumberFilter(
        field_name="tok_length", lookup_expr="gte")

    editor = django_filters.CharFilter(
        field_name="version_uri__editor", lookup_expr='icontains')
    editor_place = django_filters.CharFilter(
        field_name="version_uri__editor_place", lookup_expr='icontains')
    publisher = django_filters.CharFilter(
        field_name="version_uri__publisher", lookup_expr='icontains')
    edition_date = django_filters.CharFilter(
        field_name="version_uri__edition_date", lookup_expr='icontains')
    edition = django_filters.CharFilter(
        field_name="version_uri__ed_info", lookup_expr='icontains')
    # this field is currently always null
    language = CharInFilter(
        field_name="version_uri__version_lang", lookup_expr='in')
    tags = django_filters.CharFilter(
        field_name="version_uri__tags", lookup_expr='icontains')  # /?tags=_SHICR
    analysis_priority = CharInFilter(
        field_name="analysis_priority", lookup_expr='in')
    annotation_status = CharInFilter(
        field_name="annotation_status", lookup_expr='in')

    title_ar = django_filters.CharFilter(
        field_name="version_uri__text_id__title_ar", lookup_expr='icontains')
    title_lat = django_filters.CharFilter(
        field_name="version_uri__text_id__title_lat", lookup_expr='icontains')    
    author_ar = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__author_ar", lookup_expr='icontains')
    author_lat = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__author_lat", lookup_expr='icontains')
    died_after_AH = django_filters.NumberFilter(
        field_name="version_uri__text_id__author_id__authorDateAH", lookup_expr="gt")
    died_before_AH = django_filters.NumberFilter(
        field_name="version_uri__text_id__author_id__authorDateAH", lookup_expr="lt")
    died_between_AH = NumberRangeFilter(
        field_name="version_uri__text_id__author_id__authorDateAH", lookup_expr="range")  # /?died_between_AH=309,311
    shuhra = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__personName__shuhra", lookup_expr='icontains')
    ism = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__personName__ism", lookup_expr='icontains')
    nasab = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__personName__nasab", lookup_expr='icontains')
    kunya = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__personName__kunya", lookup_expr='icontains')
    laqab = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__personName__laqab", lookup_expr='icontains')
    nisba = django_filters.CharFilter(
        field_name="version_uri__text_id__author_id__personName__nisba", lookup_expr='icontains')

    class Meta:
        model = ReleaseMeta
        # additional fields with the default lookup ("exact"):
        fields = ["release_code", "id", "version_uri__version_uri"]
