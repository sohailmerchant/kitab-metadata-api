"""This module contains filters defined for specific views.

Filters allow specifying values for specific fields;
only results that match will be displayed. 

Documentation: https://www.django-rest-framework.org/api-guide/filtering/
"""

import datetime
import regex
# NB: use regex for regular expressions instead of re here,
#     because re does not consider Arabic vowels word characters (\w):
#     regex.findall("\w+", "أَلِفٌ")    # result: ['أَلِفٌ']
#     re.findall("\w+", "أَلِفٌ")       # result: ['أ', 'ل', 'ف']

from django_filters import rest_framework as django_filters
from rest_framework import filters
from django.db.models import Field
from django.db.models.lookups import In

from .models import Author, Text, Version, ReleaseVersion,\
      ManuscriptHolding, Manuscript
      #, PersonName, CorpusInsights, TextReuseStats


# normalization functions:
from openiti.helper.ara import normalize_ara_light
from api.util.betacode import betacodeToSearch


########################### FILTER HELPER CLASSES ####################################

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



@Field.register_lookup
class IIn(In):
    """
    Case-insensitive version of `__in` filters. Adapted from `In` and `IExact` transformers.

    See https://groups.google.com/g/django-developers/c/sFXjwyCK66A
    """

    lookup_name = 'iin'

    def process_lhs(self, *args, **kwargs):
        sql, params = super().process_lhs(*args, **kwargs)

        sql = f'LOWER({sql})'

        return sql, params

    def process_rhs(self, qn, connection):
        rhs, params = super().process_rhs(qn, connection)

        params = tuple(p.lower() for p in params)

        return rhs, params


########################### SEARCH FILTERS ####################################




def get_terms(query_string,
              findterms=regex.compile(r'"([^"]+)"|(\w+)').findall,
              normspace=regex.compile(r'\s{2,}').sub):
    """Splits the query string into individual keywords, getting rid of unnecessary spaces
    and grouping quoted words together.
    Based on: https://www.julienphalip.com/blog/adding-search-to-a-django-site-in-a-snap/
    
    Example:
        >>> get_terms(' some random words "with quotes " and spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    """
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


class CustomSearchFilter(filters.SearchFilter):
    """This custom search filter allows for normalization of the search terms,
    and allows grouping search terms using (double) quotes.
    
    Normalization is the default behaviour; if you want to switch it off, 
    add "normalize=False" to your query
    """

    def get_search_terms(self, request):
        """Override the default way Django gets the search terms;
        Add normalization + term grouping
        """
        # get the search string in the standard Django way:
        params = request.query_params.get(self.search_param, '')

        print("search params, in CustomSearchFilter:", params)
        
        # normalize the search string:
        # (if the query string does not contain "&normalize=False")
        normalize_query = request.query_params.get('normalize', '')
        if normalize_query.lower() != "false":
            params = normalize_ara_light(betacodeToSearch(params))
        
        # divide the search string into search terms (grouping words between parentheses):
        terms = get_terms(params)

        return terms

class VersionSearchFilter(CustomSearchFilter):
    """This is an implementation of the CustomSearchFilter especially for the VersionListView.
    It allows for defining specific search fields.
    """

    def get_search_fields(self, view, request):
        """Override the default way Django sets the search fields;
        give the option to use a basic set of search fields,
        a set of search fields that includes related books/persons/places,
        or a set of extended search fields."""

        # get the default search fields:
        search_fields = super().get_search_fields(view, request)
        print("VersionSearchFilter: default search fields", search_fields)

        related_search_fields = search_fields + [ 
            # ALSO SEARCH URI, TITLE AND AUTHOR NAMES OF RELATED TEXTS:
            
            "text__related_texts__text_uri", 
            "text__related_texts__titles__name", 
                # this covers the old title search fields:
                # - "text__related_texts__titles_ar", 
                # - "text__related_texts__titles_lat", 
            "text__text_related__text_uri", 
            "text__text_related__titles__name", 
                # this covers the old title search fields:
                # - "text__text_related__titles_ar", 
                # - "text__text_related__titles_lat",
            "text__related_texts__authors__names__name",
                # this covers the old title search fields:
                # - "text__related_texts__author__author_ar", 
                # - "text__related_texts__author__author_lat",
            "text__text_related__authors__names__name",
                # this covers the old title search fields:
                # - "text__text_related__author__author_ar", 
                # - "text__text_related__author__author_lat", 
           
            # ALSO SEARCH URI AND NAMES OF PERSONS RELATED TO THE TEXT:
           
            "text__related_persons__author_uri", 
            "text__related_persons__names__name",
                # this covers the old title search fields:
                # - "text__related_persons__author_ar", 
                # - "text__related_persons__author_lat",

            # ALSO SEARCH URI AND NAMES OF PERSONS RELATED TO THE AUTHOR:

            "text__authors__related_persons__author_uri", # "text__author__related_persons__author_uri", 
            "text__authors__related_persons__names__name",
                # this covers the old title search fields:
                # - "text__author__related_persons__author_ar", 
                # - "text__author__related_persons__author_lat",
            
            # ALSO SEARCH THROUGH FIELDS:
            
            "text__related_text_a__relation_type__code",
            "text__related_text_b__relation_type__code",
            "text__related_text_a__relation_type__subtype_code",
            "text__related_text_b__relation_type__subtype_code",
            "text__related_text_a__relation_type__name",
            "text__related_text_b__relation_type__name",
            "text__related_text_a__relation_type__name_inverted",
            "text__related_text_b__relation_type__name_inverted",
            "text__related_text_a__relation_type__descr",
            "text__related_text_b__relation_type__descr",
            ]

        extended_search_fields = search_fields + [
            "release_version__notes", 
            "release_version__tags", 
            "edition__ed_info",   # includes all edition fields in a single string
            "source_coll__name",  
            "source_coll__description", 
            "text__text_types__slug",# "text__text_type", 
            "text__text_types__label",# "text__text_type",
            "text__tags", 
            "text__notes"
            ]

        # check whether the user wants to use other search fields than the basic search fields:
        search_fields_q = request.query_params.get('search_fields', "")
        if not search_fields_q:
            return search_fields
        elif search_fields_q == "extended":
            search_fields = extended_search_fields
            print("SEARCHING IN EXTENDED SEARCH FIELDS!")
        elif search_fields_q == "related":
            search_fields = related_search_fields
            print("SEARCHING IN RELATED SEARCH FIELDS!")
        # perhaps a last option could be added: user/app could send the desired search fields as a comma-separated list

        return search_fields

class ReleaseVersionSearchFilter(CustomSearchFilter):
    """This is an implementation of the CustomSearchFilter especially for the VersionListView.
    It allows for defining specific search fields.
    """

    def get_search_fields(self, view, request):
        """Override the default way Django sets the search fields;
        give the option to use a basic set of search fields,
        a set of search fields that includes related books/persons/places,
        or a set of extended search fields."""

        # get the default search fields:
        search_fields = super().get_search_fields(view, request)
        print("ReleaseVersionSearchFilter default search fields:", search_fields)

        related_search_fields = search_fields + [ 
            "version__text__related_texts__text_uri", 
            "version__text__related_texts__titles__name", 
                # this covers the old title search fields:
                # - "version__text__related_texts__titles_ar", 
                # - "version__text__related_texts__titles_lat", 
            "version__text__text_related__text_uri", 
            "version__text__text_related__titles__name", 
                # this covers the old title search fields:
                # - "version__text__text_related__titles_ar", 
                # - "version__text__text_related__titles_lat",
            "version__text__related_texts__authors__names__name",
                # this covers the old title search fields:
                # - "version__text__related_texts__author__author_ar", 
                # - "version__text__related_texts__author__author_lat", 
            "version__text__text_related__authors__names__name",
                # this covers the old title search fields:
                # - "version__text__text_related__author__author_ar", 
                # - "version__text__text_related__author__author_lat",
           
            # ALSO SEARCH URI AND NAMES OF PERSONS RELATED TO THE TEXT:
           
            "version__text__related_persons__author_uri",
            "version__text__related_persons__names__name",
                # this covers the old title search fields:
                # - "version__text__related_persons__author_ar", 
                # - "version__text__related_persons__author_lat",

            # ALSO SEARCH URI AND NAMES OF PERSONS RELATED TO THE AUTHOR:
 
            "version__text__authors__related_persons__author_uri", # "version__text__author__related_persons__author_uri", 
            "version__text__authors__related_persons__names__name",
                # this covers the old title search fields:
                # - "version__text__author__related_persons__author_ar", 
                # - "version__text__author__related_persons__author_lat",
            # ALSO SEARCH THROUGH FIELDS:
            
            "version__text__related_text_a__relation_type__code",
            "version__text__related_text_b__relation_type__code",
            "version__text__related_text_a__relation_type__subtype_code",
            "version__text__related_text_b__relation_type__subtype_code",
            "version__text__related_text_a__relation_type__name",
            "version__text__related_text_b__relation_type__name",
            "version__text__related_text_a__relation_type__name_inverted",
            "version__text__related_text_b__relation_type__name_inverted",
            "version__text__related_text_a__relation_type__descr",
            "version__text__related_text_b__relation_type__descr",
            ##"version__text__authors__related_places__relation_type__code"
        ]

        extended_search_fields = search_fields + [
            "notes", 
            "tags", 
            "version__edition__ed_info",   # includes all edition fields in a single string
            "version__source_coll__name",  
            "version__source_coll__description", 
            "version__text__text_types__slug", # "version__text__text_type", 
            "version__text__text_types__label", # "version__text__text_type", 
            "version__text__tags", 
            "version__text__notes"
            ]

        # check whether the user wants to use other search fields than the basic search fields:
        search_fields_q = request.query_params.get('search_fields', "")
        if not search_fields_q:
            print("SEARCHING IN BASIC SEARCH FIELDS!")
            return search_fields
        elif search_fields_q == "extended":
            search_fields = extended_search_fields
            print("SEARCHING IN EXTENDED SEARCH FIELDS!")
        elif search_fields_q == "related":
            search_fields = related_search_fields
            print("SEARCHING IN RELATED SEARCH FIELDS!")
        # perhaps a last option could be added: user/app could send the desired search fields as a comma-separated list

        return search_fields
    



########################### VIEW FILTER CLASSES ####################################

class VersionFilter(django_filters.FilterSet):
    """Define the fields by which versions objects can be filtered.

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used 
        (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    # TO DO: find out how we can intercept the querystring and normalize it as we do in the search query

    Examples: 

    http://127.0.0.1:8000/all-releases/version/all/?died_after_AH=309&died_before_AH=311
    http://127.0.0.1:8000/all-releases/version/all/?title_ar=تاريخ
    http://127.0.0.1:8000/all-releases/version/all/?date_AH=310
    http://127.0.0.1:8000/all-releases/version/all/?author_uri=0310Tabari
    http://127.0.0.1:8000/all-releases/version/?tok_count_gte=800000&tok_count_lte=1000000
    http://127.0.0.1:8000/all-releases/version/?release_tags=NO_MAJOR_ISSUES
    http://127.0.0.1:8000/all-releases/version/?text_tags=SHICR
    http://127.0.0.1:8000/all-releases/version/?editor=العاني
    http://127.0.0.1:8000/all-releases/version/?edition=العاني&edition=الفلاح
    http://127.0.0.1:8000/all-releases/version/?language=per
    http://127.0.0.1:8000/all-releases/version/?analysis_priority=pri

    """
    def filter_name_type(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "nisba" / "nasab" / "kunya" /...)
        return (
            queryset.filter(
                text__authors__names__name_type=name,
                text__authors__names__name__icontains=value,
            )
            .distinct()
        )
    
    def filter_name_by_language(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_ar", "author_lat")
        name_or_title, language = name.split("_")
        if name_or_title == "author":
            return (
                queryset.filter(
                    text__authors__names__language=language,
                    text__authors__names__name__icontains=value,
                )
                .distinct()
            )
        elif name_or_title == "title":
            return (
                queryset.filter(
                    text__titles__language=language,
                    text__titles__name__icontains=value,
                )
                .distinct()
            )


    def filter_by_date(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_died_before_AH", "author_died_after_CE", ...)
        
        try:
            _, date_type, condition, calendar = name.split("_")
        except:
            date_type, condition, calendar = name.split("_")
        
        author_prefix = "text__authors__"
        ed_prefix = "edition__"
        if date_type in ("born", "died"):
            if date_type == "died":
                code = "death_date"
            elif date_type == "born":
                code = "birth_date"
            path = f"{author_prefix}dates"
        elif date_type == "edited":
            code = "edited"
            path = f"{ed_prefix}dates"

        if calendar == "CE":
            if condition == "before":
                value = datetime.date(int(value),12,31)
                year = "ce_end"
            elif condition == "after":
                value = datetime.date(int(value),1,1)
                year = "ce_start"
            if condition == "between":
                v1 = datetime.date(int(value[0]),1,1)
                v2 = datetime.date(int(value[1]),1,1)
                value = (v1, v2)
                year = "ce_start"
            base = queryset
            
        else:
            year = "year"
            base = queryset.filter(**{
                f"{path}__calendar__slug": calendar,
                f"{path}__date_type__slug": code,
            })
        
        if condition == "after":
            return base.filter(**{f"{path}__{year}__gte": value}).distinct()
        elif condition == "before":
            return base.filter(**{f"{path}__{year}__lte": value}).distinct()
        elif condition == "between":
            return base.filter(**{f"{path}__{year}__range": value}).distinct()

    version_uri_contains = django_filters.CharFilter(
        field_name="version_uri", lookup_expr='icontains', label="Version URI") 
    version_uri = django_filters.CharFilter(
        field_name="version_uri", lookup_expr='icontains', label="Version URI")  
    version_code = django_filters.CharFilter(
        field_name="version_code", lookup_expr='icontains', label="Version code") 
    
    subcorpus = django_filters.CharFilter(lookup_expr='icontains',
        field_name="release_version__subcorpus", label="Subcorpus (ara, per, mss, ...)") 
    language = CharInFilter(lookup_expr='iin',    # case insensitive version of "in"
        field_name="language", label="Language (three-letter code, separate multiple options with comma)")
    uncorrected_ocr = django_filters.BooleanFilter(field_name="release_version__uncorrected_ocr", 
        label="Was this text created using OCR, without manual correction?")
    analysis_priority = CharInFilter(lookup_expr='iin',    # case insensitive version of "in"
        field_name="release_version__analysis_priority", label="Analysis priority (pri/sec)")
    annotation_status = CharInFilter(lookup_expr='iin',  # case insensitive version of "in"
        field_name="release_version__annotation_status", label="Annotation status (inProgress/completed/mARkdown/(not yet annotated))")

    release_tags = django_filters.CharFilter(
        field_name="release_version__tags", lookup_expr='icontains',
        label="Tags related to the digital version")
    text_tags = django_filters.CharFilter(
        field_name="text__tags", lookup_expr='icontains',
        label="Tags related to the text")  # /?tags=_SHICR
    
    
    
    author_uri = django_filters.CharFilter(
        field_name="text__authors__author_uri", lookup_expr='icontains',
        label="Author URI")
    author = django_filters.CharFilter(
        field_name="text__authors__names__name", lookup_expr='icontains',
        label="Author name (Arabic/Latin script)")
    author_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Arabic script)"
    )
    author_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Latin script)"
    )
    shuhra = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's shuhra (Arabic or Latin script)"
    )
    ism = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's ism (Arabic or Latin script)"
    )
    nasab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nasab (Arabic or Latin script)"
    )
    kunya = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's kunya (Arabic or Latin script)"
    )
    laqab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's laqab (Arabic or Latin script)"
    )
    nisba = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nisba (Arabic or Latin script)"
    )

    author_died_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (AH)",
    )
    author_died_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (AH)",
    )
    author_died_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (AH)",
    ) # /?died_between_AH=309,311

    author_born_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (AH)",
    )
    author_born_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (AH)",
    )
    author_born_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (AH)",
    ) # /?died_between_AH=309,311

    
    author_died_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (CE)",
    )
    author_died_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (CE)",
    )
    author_died_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (CE)",
    ) # /?died_between_CE=890,892

    author_born_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (CE)",
    )
    author_born_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (CE)",
    )
    author_born_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (CE)",
    ) # /?died_between_CE=890,892


    title = django_filters.CharFilter(
        field_name="text__titles__name", lookup_expr='icontains',
        label="Title (Arabic/Latin script)"
    )
    title_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title (Arabic script)"
    )
    title_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title (Latin script)"
    )

    tok_count_lte = django_filters.NumberFilter(
        field_name="release_version__tok_length", lookup_expr="lte", 
        label="Token (word) count is less than or equal to")
    tok_count_gte = django_filters.NumberFilter(
        field_name="release_version__tok_length", lookup_expr="gte", 
        label="Token (word) count is greater than or equal to")
    char_count_lte = django_filters.NumberFilter(
        field_name="release_version__char_length", lookup_expr="lte", 
        label="Character count is less than or equal to")
    char_count_gte = django_filters.NumberFilter(
        field_name="release_version__char_length", lookup_expr="gte", 
        label="Character count is greater than or equal to")

    editor = django_filters.CharFilter(
        field_name="edition__editor", lookup_expr='icontains',
        label="Editor")
    publisher = django_filters.CharFilter(
        field_name="edition__publisher", lookup_expr='icontains',
        label="Publisher")
    edition_place = django_filters.CharFilter(
        field_name="edition__edition_place", lookup_expr='icontains',
        label="Place of Edition")
    
    edition = django_filters.CharFilter(
        field_name="edition__ed_info", lookup_expr='icontains',
        label="All edition-related metadata")
    edition_date = django_filters.CharFilter(
        field_name="edition__dates__date_str", lookup_expr='icontains',
        label="Date of Edition")
    edited_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition before (AH)",
    )
    edited_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition after (AH)",
    )
    edited_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Date of edition between (AH)",
    )
    edited_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition before (CE)",
    )
    edited_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition after (CE)",
    )
    edited_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Date of edition between (CE)",
    )
    
    manuscript_uri = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript__manuscript_uri", label="Manuscript URI")
    shelfmark = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript__shelfmark", label="Shelfmark")
    manuscript_type = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript__manuscript_types__label", label="Manuscript type")
    script = django_filters.CharFilter(lookup_expr='icontains',
        field_name="script", label="Script")
    manuscript_title = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript__titles__name", label="Title of the manuscript")


    class Meta:
        model = Version
        # additional fields with the default lookup ("exact"):
        fields = ["id"]




class AuthorFilter(django_filters.FilterSet):
    """Define the fields by which author objects can be filtered.

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
    def filter_name_type(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "nisba" / "nasab" / "kunya" /...)
        return (
            queryset.filter(
                names__name_type=name,
                names__name__icontains=value,
            )
            .distinct()
        )
    
    def filter_name_by_language(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_ar", "author_lat")
        try:
            name_or_title, language = name.split("_")
        except:
            _, name_or_title, language = name.split("_")
        if name_or_title == "author":
            return (
                queryset.filter(
                    names__language=language,
                    names__name__icontains=value,
                )
                .distinct()
            )
        elif name_or_title == "title":  
            return (
                queryset.filter(
                    texts__titles__language=language,
                    texts__titles__name__icontains=value,
                )
                .distinct()
            )

    def filter_by_date(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "died_before_AH", "died_after_CE", ...)
        date_type, condition, calendar = name.split("_")
        
        author_prefix = ""
        ed_prefix = "texts__version__edition__"
        
        if date_type in ("born", "died"):
            if date_type == "died":
                code = "death_date"
            elif date_type == "born":
                code = "birth_date"
            path = f"{author_prefix}dates"
        elif date_type == "edited": # TODO
            code = "edited"
            path = f"{ed_prefix}dates"

        if calendar == "CE":
            if condition == "before":
                value = datetime.date(int(value),12,31)
                year = "ce_end"
            elif condition == "after":
                value = datetime.date(int(value),1,1)
                year = "ce_start"
            if condition == "between":
                v1 = datetime.date(int(value[0]),1,1)
                v2 = datetime.date(int(value[1]),1,1)
                value = (v1, v2)
                year = "ce_start"
            base = queryset
            
        else:
            year = "year"
            base = queryset.filter(**{
                f"{path}__calendar__slug": calendar,
                f"{path}__date_type__slug": code,
            })
        
        if condition == "after":
            return base.filter(**{f"{path}__{year}__gte": value}).distinct()
        elif condition == "before":
            return base.filter(**{f"{path}__{year}__lte": value}).distinct()
        elif condition == "between":
            return base.filter(**{f"{path}__{year}__range": value}).distinct()


    author_uri = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="author_uri", label="Author URI"
    ) 
    author = django_filters.CharFilter(
        field_name="names__name", lookup_expr='icontains',
        label="Author name (Arabic/Latin script)"
    )
    author_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Arabic script)"
    )
    author_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Latin script)"
    )
    shuhra = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's shuhra (Arabic or Latin script)"
    )
    ism = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's ism (Arabic or Latin script)"
    )
    nasab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nasab (Arabic or Latin script)"
    )
    kunya = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's kunya (Arabic or Latin script)"
    )
    laqab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's laqab (Arabic or Latin script)"
    )
    nisba = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nisba (Arabic or Latin script)"
    )
    

    died_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (AH)",
    )
    died_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (AH)",
    )
    died_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (AH)",
    ) # /?died_between_AH=309,311

    born_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (AH)",
    )
    born_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (AH)",
    )
    born_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (AH)",
    ) # /?died_between_AH=309,311

    
    died_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (CE)",
    )
    died_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (CE)",
    )
    died_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (CE)",
    ) # /?died_between_CE=890,892

    born_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (CE)",
    )
    born_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (CE)",
    )
    born_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (CE)",
    ) # /?died_between_CE=890,892

    subcorpus = django_filters.CharFilter(lookup_expr='icontains',
        field_name="texts__version__release_version__subcorpus", label="Subcorpus (ara, per, mss, ...)") 
    language = django_filters.CharFilter(lookup_expr='icontains',
        field_name="texts__version__language", label="Language code of the text (are, per, ...)")
    

    text_title = django_filters.CharFilter(
        field_name="texts__titles__name", lookup_expr='icontains',
        label="Title of work (Arabic/Latin script)"
    )
    text_title_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title of work (Arabic script)"
    )
    text_title_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title of work (Latin script)"
    )
   
    class Meta:
        model = Author
        # additional fields with the default lookup ("exact"):
        fields = ["id"]


class ManuscriptHoldingFilter(django_filters.FilterSet):
    """Define the fields by which ManuscriptHolding objects can be filtered.

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 

    http://127.0.0.1:8000/ms-holding/all/?loc_uri=MS0044LondonKhalili

    """
    loc_uri = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="loc_uri", label="Manuscript holding URI")
    name = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="names__name", label="Manuscript holding name")
    country = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="country__names__name", label="Manuscript holding country")
    city = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="city__names__name", label="Manuscript holding city")
    
    manuscript_uri = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__manuscript_uri", label="Manuscript URI")
    shelfmark = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__shelfmark", label="Manuscript shelfmark")
    manuscript_type = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__manuscript_types__slug", label="Manuscript type")
    title = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__titles__name", label="Manuscript title")
    text = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__related_texts__titles__name", label="Text title")
    author = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__related_persons__names__name", label="Text author")
    text_uri = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__related_texts__text_uri", label="Text URI")
    author_uri = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="manuscript__related_persons__author_uri", label="Author URI")
    
    # TODO: writing_place, writing_date_AH, writing_date_CE, ...


    class Meta:
        model = ManuscriptHolding
        # additional fields with the default lookup ("exact"):
        fields = ["id"]

class ManuscriptFilter(django_filters.FilterSet):
    """Define the fields by which manuscript objects can be filtered.

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/manuscript/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/manuscript/?title_ar=تاريخ
    http://127.0.0.1:8000/manuscript/?date_AH=310
    http://127.0.0.1:8000/manuscript/?author_uri=0310Tabari

    """

    def filter_persons(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_uri" / "copyist_name" / ...)
        person_type, field = name.split("_")
        if person_type == "author":
            relation_code = "AUTH"
        elif person_type == "copyist":
            relation_code = "COPY"
        return (
            queryset.filter(**{
                "related_manuscript_b__relation_type__code": relation_code,
                "related_manuscript_b__person_a__names__name__icontains": value,
            })
            .distinct()
        )
    
    def filter_by_date(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "copied_before_AH", "copied_after_CE", ...)
        date_type, condition, calendar = name.split("_")
        if date_type == "copied": # TODO
            code = "COPY"
            path = "dates"
        
        if calendar == "CE":
            if condition == "before":
                value = datetime.date(int(value),12,31)
                year = "ce_end"
            elif condition == "after":
                value = datetime.date(int(value),1,1)
                year = "ce_start"
            if condition == "between":
                v1 = datetime.date(int(value[0]),1,1)
                v2 = datetime.date(int(value[1]),1,1)
                value = (v1, v2)
                year = "ce_start"
            base = queryset
        else:
            base = queryset.filter(**{
                f"{path}__calendar__slug": calendar,
                f"{path}__date_type__slug": code,
            })
            year = "year"
        if condition == "after":
            return base.filter(**{f"{path}__{year}__gte": value}).distinct()
        elif condition == "before":
            return base.filter(**{f"{path}__{year}__lte": value}).distinct()
        elif condition == "between":
            return base.filter(**{f"{path}__{year}__range": value}).distinct()


    manuscript_uri = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript_uri", label="Manuscript URI")
    shelfmark = django_filters.CharFilter(lookup_expr='icontains',
        field_name="shelfmark", label="Shelfmark")
    manuscript_type = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript_types__label", label="Manuscript type")
    script = django_filters.CharFilter(lookup_expr='icontains',
        field_name="script", label="Script")
    tag = django_filters.CharFilter(field_name="tags", lookup_expr='icontains')
    title = django_filters.CharFilter(lookup_expr='icontains',
        field_name="titles__name", label="Title of the manuscript")
    
    language = django_filters.CharFilter(lookup_expr='icontains',
        field_name="transcription__language", label="Language code of the text (are, per, ...)")

    text_uri = django_filters.CharFilter(lookup_expr='icontains',
        field_name="related_manuscript_a__text_b__text_uri", label="Text URI")
    text_title = django_filters.CharFilter(lookup_expr='icontains',
        field_name="related_manuscript_a__text_b__titles__name", 
        label="Title of a text contained in the manuscript")
    place = django_filters.CharFilter(lookup_expr='icontains',
        field_name="related_places__names__name", 
        label="Place related to the manuscript")
    copied_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Manuscript copied before (AH)")
    copied_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Manuscript copied after (AH)")
    copied_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="manuscript copied between (AH)")
    copied_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Manuscript copied before (CE)")
    copied_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Manuscript copied after (CE)")
    copied_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="manuscript copied between (CE)")
    
    manuscript_holding= django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript_holding__names__name", 
        label="Manuscript holding institution")
    country = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript_holding__country__names__name", 
        label="Manuscript holding country")
    city = django_filters.CharFilter(lookup_expr='icontains',
        field_name="manuscript_holding__city__names__name", 
        label="Manuscript holding city")
           
    author = django_filters.CharFilter(
        method="filter_persons",
        label="Author name",
    )
    copyist = django_filters.CharFilter(
        method="filter_persons",
        label="Copyist name",
    )
    
    # author_died_after_AH = django_filters.NumberFilter(lookup_expr="gt",          # /?died_after_AH=309
    #     field_name="author__date_AH", label="Author died after the hijrī year")  
    # author_died_before_AH = django_filters.NumberFilter(lookup_expr="lt",         # /?died_before_AH=311
    #     field_name="author__date_AH", label="Author died before the hijrī year")  
    # author_died_between_AH = NumberRangeFilter(lookup_expr="range",               # /?died_between_AH=309,311
    #     field_name="author__date_AH", label="Author died between the hijrī years (comma-separated)")       

    class Meta:
        model = Manuscript
        # additional fields with the default lookup ("exact"):
        fields = ["id"]

class TextFilter(django_filters.FilterSet):
    """Define the fields by which text objects can be filtered.

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/text/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/author/?title_ar=تاريخ
    http://127.0.0.1:8000/author/?date_AH=310
    http://127.0.0.1:8000/author/?author_uri=0310Tabari

    """
    def filter_name_type(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "nisba" / "nasab" / "kunya" /...)
        _, name_type = name.split("_")
        return (
            queryset.filter(
                authors__names__name_type=name_type,
                authors__names__name__icontains=value,
            )
            .distinct()
        )
    
    def filter_name_by_language(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_ar", "title_lat")
        name_or_title, language = name.split("_")
        
        if name_or_title == "author":
            return (
                queryset.filter(
                    authors__names__language=language,
                    authors__names__name__icontains=value,
                )
                .distinct()
            )
        elif name_or_title == "title":  
            return (
                queryset.filter(
                    titles__language=language,
                    titles__name__icontains=value,
                )
                .distinct()
            )


    def filter_by_date(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "died_before_AH", "died_after_CE", ...)
        _, date_type, condition, calendar = name.split("_")
        author_prefix = "authors__"
        ed_prefix = "version__edition__"
        
        if date_type in ("born", "died"):
            if date_type == "died":
                code = "death_date"
            elif date_type == "born":
                code = "birth_date"
            path = f"{author_prefix}dates"
        elif date_type == "edited": # TODO
            code = "edited"
            path = f"{ed_prefix}dates"

        if calendar == "CE":
            if condition == "before":
                value = datetime.date(int(value),12,31)
                year = "ce_end"
            elif condition == "after":
                value = datetime.date(int(value),1,1)
                year = "ce_start"
            if condition == "between":
                v1 = datetime.date(int(value[0]),1,1)
                v2 = datetime.date(int(value[1]),1,1)
                value = (v1, v2)
                year = "ce_start"
            base = queryset
        else:
            year = "year"
            base = queryset.filter(**{
                f"{path}__calendar__slug": calendar,
                f"{path}__date_type__slug": code,
            })
        
        if condition == "after":
            return base.filter(**{f"{path}__{year}__gte": value}).distinct()
        elif condition == "before":
            return base.filter(**{f"{path}__{year}__lte": value}).distinct()
        elif condition == "between":
            return base.filter(**{f"{path}__{year}__range": value}).distinct()

    text_uri = django_filters.CharFilter(lookup_expr='icontains',
        field_name="text_uri", label="Text URI")
    title = django_filters.CharFilter(lookup_expr='icontains',
        field_name="titles__name", label="Title (Arabic/Latin script)")
    title_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title (Arabic script)")
    title_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title (Latin script)")
    text_type = django_filters.CharFilter(lookup_expr='icontains', 
        field_name="text_types__slug", label="Text type (book/document)")
    tag = django_filters.CharFilter(field_name="tags", lookup_expr='icontains')

    subcorpus = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__release_version__subcorpus", label="Subcorpus (ara, per, mss, ...)") 
    language = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__language", label="Language code of the text (are, per, ...)")
    
    author_died_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (AH)")  
    author_died_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (AH)")  
    author_died_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (AH)")
    author_died_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (CE)")  
    author_died_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (CE)")  
    author_died_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (CE)")      

    author = django_filters.CharFilter(lookup_expr='icontains',
        field_name="authors__names__name", 
        label="Author name (Arabic/Latin script)")
    author_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Arabic script)")
    author_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Latin script)")
    author_shuhra = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's shuhra (Arabic or Latin script)")
    author_ism = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's ism (Arabic or Latin script)")
    author_nasab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nasab (Arabic or Latin script)")
    author_kunya = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's kunya (Arabic or Latin script)")
    author_laqab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's laqab (Arabic or Latin script)")
    author_nisba = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nisba (Arabic or Latin script)")

    related_title = django_filters.CharFilter(lookup_expr='icontains',
        field_name="related_texts__titles__name", 
        label="Title (Arabic/Latin script)")

    class Meta:
        model = Text
        # additional fields with the default lookup ("exact"):
        fields = ["id"]

# BUILDUP: UNCOMMENT:
# class TextReuseFilter(django_filters.FilterSet):
#     """Filters for views based on the TextReuseStats model
    
#     Examples:
#     http://127.0.0.1:7000/2022.2.7/text-reuse-stats/?book_1=Tabari  # any part of the version URI
#     http://127.0.0.1:7000/2022.2.7/text-reuse-stats/?book_2=Shamela # any part of the version URI
#     http://127.0.0.1:7000/2022.2.7/text-reuse-stats/?book_1_in=Shamela0009783BK1,Shamela0009783BK4
#     http://127.0.0.1:7000/2022.2.7/text-reuse-stats/?instances_count_gt=500  # pairs with more than 500 text reuse instances
#     http://127.0.0.1:7000/2022.2.7/text-reuse-stats/?instances_count_range_min=500&instances_count_range_max=600
#     http://127.0.0.1:7000/2022.2.7/text-reuse-stats/?book2_words_matched_gt=100000 # pairs with more than 100.000 words matched in book 2
#     http://127.0.0.1:7000/2022.2.7/text-reuse-stats/?book1_pct_words_matched_gt=0.8 # pairs with more than 80% of book 1 in book 2
#     """
#     # filter on version URI: 
#     book_1 = django_filters.CharFilter(lookup_expr='icontains', 
#         field_name="book_1__version__version_uri", label="Version URI of book 1")
#     book_2 = django_filters.CharFilter(lookup_expr='icontains', 
#         field_name="book_2__version__version_uri", label="Version URI of book 2")
#     book_1_in = CharInFilter(lookup_expr='in', 
#         field_name="book_1__version__version_code", label="Comma-separated list of book 1 genre codes")
#     book_2_in = CharInFilter(lookup_expr='in', 
#         field_name="book_2__version__version_code", label="Comma-separated list of book 2 genre codes")
    
#     # filter on the number of text reuse instances:
#     instances_count_gt = django_filters.NumberFilter(lookup_expr="gt", 
#         field_name="instances_count", label="Minimum number of text reuse instances")
#     instances_count_lt = django_filters.NumberFilter(lookup_expr="lt",
#         field_name="instances_count", label="Maximum number of text reuse instances")
#     instances_count_range = django_filters.NumericRangeFilter(lookup_expr="range",
#         field_name="instances_count", label="Number of text reuse instances between")
#     # NB: example of the range filter in url query string: 
#     # ?instances_count_range_min=10&instances_count_range_max=80

#     # filter on the number of words in book 1 that are matched in book 2:
#     book1_words_matched_gt = django_filters.NumberFilter(lookup_expr="gt", 
#         field_name="book1_words_matched_max", 
#         label="Minimum number of words of book 1 found in text reuse instances with book 2")
#     book1_words_matched_lt = django_filters.NumberFilter(lookup_expr="lt",
#         field_name="book1_words_matched_min",
#         label="Maximum number of words of book 1 found in text reuse instances with book 2")
#     book1_words_matched_range = django_filters.NumericRangeFilter(lookup_expr="range",
#         field_name="book1_words_matched_between", 
#         label="Number of words of book 1 found in text reuse instances with book 2 (between)")

#     # filter on the number of words in book 2 that are matched in book 1:
#     book2_words_matched_gt = django_filters.NumberFilter(lookup_expr="gt", 
#         field_name="book2_words_matched_max", 
#         label="Minimum number of words of book 2 found in text reuse instances with book 1")
#     book2_words_matched_lt = django_filters.NumberFilter(lookup_expr="lt",
#         field_name="book2_words_matched_min",
#         label="Maximum number of words of book 2 found in text reuse instances with book 1")
#     book2_words_matched_range = django_filters.NumericRangeFilter(lookup_expr="range",
#         field_name="book2_words_matched_between", 
#         label="Number of words of book 2 found in text reuse instances with book 1 (between)")

#     # filter on the percentage of words in book 1 that are matched in book 2:
#     book1_pct_words_matched_gt = django_filters.NumberFilter(lookup_expr="gt", 
#         field_name="book1_pct_matched_max", 
#         label="Minimum percentage of words of book 1 found in text reuse instances with book 2")
#     book1_pct_words_matched_lt = django_filters.NumberFilter(lookup_expr="lt",
#         field_name="book1_pct_matched_min",
#         label="Maximum percentage of words of book 1 found in text reuse instances with book 2")
#     book1_pct_words_matched_range = django_filters.NumericRangeFilter(lookup_expr="range",
#         field_name="book1_pct_matched_between", 
#         label="Percentage of words of book 1 found in text reuse instances with book 2 (between)")

#     # filter on the percentage of words in book 2 that are matched in book 1:
#     book2_pct_words_matched_gt = django_filters.NumberFilter(lookup_expr="gt", 
#         field_name="book2_pct_matched_max", 
#         label="Minimum percentage of words of book 2 found in text reuse instances with book 1")
#     book2_pct_words_matched_lt = django_filters.NumberFilter(lookup_expr="lt",
#         field_name="book2_pct_matched_min",
#         label="Maximum percentage of words of book 2 found in text reuse instances with book 1")
#     book2_pct_words_matched_range = django_filters.NumericRangeFilter(lookup_expr="range",
#         field_name="book2_pct_matched_between", 
#         label="Percentage of words of book 2 found in text reuse instances with book 1 (between)")

#     class Meta:
#         model = TextReuseStats
#         # additional fields with the default lookup ("exact"):
#         fields = ["id"]


class ReleaseVersionFilter(django_filters.FilterSet):
    """Define the filter fields that can be looked up for versions

    The variable name will be used in the query in the URL;
    the field name is the name of the field in the model;
    and the lookup_expr defines which lookup method must be used (lt = less than, gt = greater than,
        icontains = case insensitive substring)

    E.g., 
    http://127.0.0.1:8000/2025.1.9/version/all/?died_after_AH=309&died_before_AH=310
    http://127.0.0.1:8000/2025.1.9/version/all/?book_title_ar=تاريخ
    http://127.0.0.1:8000/2025.1.9/version/all/?date_AH=310
    http://127.0.0.1:8000/2025.1.9/version/all/?author_uri=0310Tabari

    """

    def filter_name_type(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_nisba" / "author_nasab" / "author_kunya" /...)
        _, name = name.split("_")
        return (
            queryset.filter(
                version__text__authors__names__name_type=name,
                version__text__authors__names__name__icontains=value,
            )
            .distinct()
        )
    
    def filter_name_by_language(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_ar", "author_lat")
        name_or_title, language = name.split("_")
        if name_or_title == "author":
            return (
                queryset.filter(
                    version__text__authors__names__language=language,
                    version__text__authors__names__name__icontains=value,
                )
                .distinct()
            )
        elif name_or_title == "title":
            return (
                queryset.filter(
                    version__text__titles__language=language,
                    version__text__titles__name__icontains=value,
                )
                .distinct()
            )


    def filter_by_date(self, queryset, name, value):
        # here `name` is the key in the query string 
        # (will be "author_died_before_AH", "author_died_after_CE", ...)
        try:
            _, date_type, condition, calendar = name.split("_")
        except:
            date_type, condition, calendar = name.split("_")
        
        author_prefix = "version__text__authors__"
        ed_prefix = "version__edition__"
        if date_type in ("born", "died"):
            if date_type == "died":
                code = "death_date"
            elif date_type == "born":
                code = "birth_date"
            path = f"{author_prefix}dates"
        elif date_type == "edited":
            code = "edited"
            path = f"{ed_prefix}dates"

        if calendar == "CE":
            if condition == "before":
                value = datetime.date(int(value),12,31)
                year = "ce_end"
            elif condition == "after":
                value = datetime.date(int(value),1,1)
                year = "ce_start"
            if condition == "between":
                v1 = datetime.date(int(value[0]),1,1)
                v2 = datetime.date(int(value[1]),1,1)
                value = (v1, v2)
                year = "ce_start"
            base = queryset
            
        else:
            year = "year"
            base = queryset.filter(**{
                f"{path}__calendar__slug": calendar,
                f"{path}__date_type__slug": code,
            })
        
        if condition == "after":
            return base.filter(**{f"{path}__{year}__gte": value}).distinct()
        elif condition == "before":
            return base.filter(**{f"{path}__{year}__lte": value}).distinct()
        elif condition == "between":
            return base.filter(**{f"{path}__{year}__range": value}).distinct()

    version_code = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__version_code", label="Version URI contains")  # "exact" is default
    version_uri = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__version_uri", label="Version URI contains")  # "exact" is default
    char_count_lte = django_filters.NumberFilter(lookup_expr="lte",
        field_name="char_length", label="Maximum character count")
    char_count_gte = django_filters.NumberFilter(lookup_expr="gte",
        field_name="char_length", label="Minimum character count")
    tok_count_lte = django_filters.NumberFilter(lookup_expr="lte",
        field_name="tok_length", label="Maximum token count")
    tok_count_gte = django_filters.NumberFilter(lookup_expr="gte",
        field_name="tok_length", label="Minimum token count")

    editor = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__edition__editor", label="Editor of the paper version")
    edition_place = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__edition__edition_place", label="Place of the edition of the paper version")
    publisher = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__edition__publisher", label="Publisher of the paper version")
    edition_date = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__edition__edition_date", label="Edition date of the paper version")
    edition = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__edition__ed_info", label="Any information on the edition of the paper version")

    subcorpus = django_filters.CharFilter(lookup_expr='icontains',
        field_name="subcorpus", label="Subcorpus (ara, per, mss, ...)") 
    language = django_filters.CharFilter(lookup_expr='icontains',    # case insensitive version of "in"
        field_name="version__language", label="Language (three-letter code, separate multiple options with comma)")
    uncorrected_ocr = django_filters.BooleanFilter(field_name="uncorrected_ocr", 
        label="Was this text created using OCR, without manual correction?")
    tags = django_filters.CharFilter(lookup_expr='icontains',
        field_name="tags", label="Version tags contain")  # /?tags=_SHICR
    text_tags = django_filters.CharFilter(
        field_name="version__text__tags", lookup_expr='icontains',
        label="Tags related to the text")  # /?text_tags=_SHICR
    analysis_priority = CharInFilter(lookup_expr='iin',    # case insensitive version of "in"
        field_name="analysis_priority", label="Analysis priority (pri/sec)")
    annotation_status = CharInFilter(lookup_expr='iin',  # case insensitive version of "in"
        field_name="annotation_status", label="Annotation status (inProgress/completed/mARkdown/(not yet annotated))")

    author = django_filters.CharFilter(
        field_name="version__text__authors__names__name", lookup_expr='icontains',
        label="Author name (Arabic/Latin script)")
    author_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Arabic script)"
    )
    author_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Author name (Latin script)"
    )
    author_shuhra = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's shuhra (Arabic or Latin script)"
    )
    author_ism = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's ism (Arabic or Latin script)"
    )
    author_nasab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nasab (Arabic or Latin script)"
    )
    author_kunya = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's kunya (Arabic or Latin script)"
    )
    author_laqab = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's laqab (Arabic or Latin script)"
    )
    author_nisba = django_filters.CharFilter(
        method="filter_name_type",
        label="Author's nisba (Arabic or Latin script)"
    )
    author_died_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (AH)")  
    author_died_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (AH)")  
    author_died_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (AH)") 
    author_died_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died after (CE)")  
    author_died_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Author died before (CE)")  
    author_died_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Author died between (CE)") 
    
    title = django_filters.CharFilter(
        field_name="version__text__titles__name", lookup_expr='icontains',
        label="Title (Arabic/Latin script)")
    title_ar = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title (Arabic script)"
    )
    title_lat = django_filters.CharFilter(
        method="filter_name_by_language",
        label="Title (Latin script)"
    )  
    
    editor = django_filters.CharFilter(
        field_name="version__edition__editor", lookup_expr='icontains',
        label="Editor")
    publisher = django_filters.CharFilter(
        field_name="version__edition__publisher", lookup_expr='icontains',
        label="Publisher")
    edition_place = django_filters.CharFilter(
        field_name="version__edition__edition_place", lookup_expr='icontains',
        label="Place of Edition")
    
    edition = django_filters.CharFilter(
        field_name="version__edition__ed_info", lookup_expr='icontains',
        label="All edition-related metadata")
    edition_date = django_filters.CharFilter(
        field_name="version__edition__dates__date_str", lookup_expr='icontains',
        label="Date of Edition")
    edited_before_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition before (AH)",
    )
    edited_after_AH = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition after (AH)",
    )
    edited_between_AH = NumberRangeFilter(
        method="filter_by_date",
        label="Date of edition between (AH)",
    )
    edited_before_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition before (CE)",
    )
    edited_after_CE = django_filters.NumberFilter(
        method="filter_by_date",
        label="Date of edition after (CE)",
    )
    edited_between_CE = NumberRangeFilter(
        method="filter_by_date",
        label="Date of edition between (CE)",
    )

    manuscript_uri = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__manuscript__manuscript_uri", label="Manuscript URI")
    shelfmark = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__manuscript__shelfmark", label="Shelfmark")
    manuscript_type = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__manuscript__manuscript_types__label", label="Manuscript type")
    script = django_filters.CharFilter(lookup_expr='icontains',
        field_name="script", label="Script")
    manuscript_title = django_filters.CharFilter(lookup_expr='icontains',
        field_name="version__manuscript__titles__name", label="Title of the manuscript")

    
    
    class Meta:
        model = ReleaseVersion
        # additional fields with the default lookup ("exact"):
        fields = ["id", "version"]
