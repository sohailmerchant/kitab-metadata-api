"""
This module contains view classes and functions.

Views take web requests as input and return a response;
in our API, the requests are database queries;
the response could be an HTML page, 
but in our API the response is a JSON representation
(serialization) of the results returned by the database)

Documentation: 
* https://docs.djangoproject.com/en/4.2/topics/http/views/
* https://docs.djangoproject.com/en/4.2/topics/class-based-views/
* https://www.django-rest-framework.org/api-guide/views/#class-based-views
* https://www.django-rest-framework.org/api-guide/views/#function-based-views
"""

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404

from rest_framework import generics, status
from rest_framework import pagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from rest_framework import serializers
from django_filters import rest_framework as django_filters


from .models import Author, PersonName, Text, Version, CorpusInsights, \
                    TextReuseStats, A2BRelation, ReleaseVersion, SourceCollectionDetails,\
                    ReleaseInfo, RelationType, GitHubIssue
from .serializers import TextSerializer, VersionSerializer, PersonNameSerializer, ReleaseVersionSerializer, \
                         AuthorSerializer, TextReuseStatsSerializer, CorpusInsightsSerializer, \
                         AllRelationsSerializer,  SourceCollectionDetailsSerializer, ReleaseInfoSerializer, \
                         ShallowTextReuseStatsSerializer, TextReuseStatsSerializerB1, AllRelationTypesSerializer, \
                         GitHubIssueSerializer
from .filters import AuthorFilter, VersionFilter, TextFilter, TextReuseFilter, ReleaseVersionFilter, \
                     CustomSearchFilter, VersionSearchFilter, ReleaseVersionSearchFilter

# list all parameters (apart from view-specific filters)
# that are allowed in a URL's querystring
# (other parameters will throw an error):
allowed_parameters = [
    "search", 
    "normalize",     # allowed options: "true" (default), "false"
    "ordering", 
    "page", 
    "page_size",
    "fields",
    "search_fields"  # allowed options: "related", "extended"
] 


# fields to be excluded from search (because they are not string fields):
excl_flds = [
    # numeric fields:
    "id", "date", "date_AH", "date_CE", "tok_length", "char_length",
    # foreign key fields:
    "text", "name_element", "version", "author", "text", "version_info",
    "related_persons", "related_places", "related_texts", "place_relations",
    "person_a", "person_b", "text_a", "text_b",
    "place_a", "place_b", "relation_type", "parent_type",
    # related fields:
    'authormeta', 'textmeta', 'related_person_a', 'related_person_b',
    "related_text_a", "related_text_b"]



class CustomPagination(PageNumberPagination):
    """Add customizable pagination to a list of results.
    
    A specific page can be accessed using the "page=" parameter:
    http://127.0.0.1:7000/2022.2.7/version/all/?page=12

    By default, 10 items are displayed per page; the user can change this using the "page_size=" querystring parameter
    http://127.0.0.1:7000/2022.2.7/version/all/?page_size=50

    Documentation: https://www.django-rest-framework.org/api-guide/pagination/#pagenumberpagination
    """
    # set number of results per page by default to 10:
    page_size = 10

    # set a query string parameter that can be used to change the number of items per page:
    # (e.g., http://127.0.0.1:7000/2022.2.7/version/all/?page_size=50)
    page_size_query_param = 'page_size'

    # set the maximum number of items per page (even if user requests larger page_size):
    max_page_size = 200

    # set the strings that can be used to request the last page in the set:
    # (e.g., http://127.0.0.1:7000/2022.2.7/version/all/?page=last)
    last_page_strings = ('the_end', 'last')

    def get_paginated_response(self, data):
        """Customize how the paginated list looks. 
        
        Documentation: https://www.django-rest-framework.org/api-guide/pagination/#custom-pagination-styles
        """

        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'page_size': self.page.paginator.per_page,
            'has_pages': self.page.has_next(),
            'count': self.page.paginator.count,
            'pages': self.page.paginator.num_pages,
            'results': data
        })


class CustomListView(generics.ListAPIView):
    """
    Display the results as a paginated list.
    Filter, sort and search are enabled, and fields to be displayed can be specified.

    To create a ListView with filtering, sorting, search and pagination: 
    define a subclass of this class (e.g., `class VersionListView(CustomListView):`)

    Examples: 
        /version/all/
        /version/all/?fields=version_uri,version_code   # get only these two fields!
        /version/all/?search=JK000001
        /version/all/?search=JK000001&normalize=False   # 
        /version/all/?ordering=version_uri
        /version/all/?page=2
        /version/all/?page_size=100     # default: 10, max: 200
        /version/all/?fields=version_code&search=JK000001&page=2
    """
    pagination_class = CustomPagination    # number of pages can be controlled via the "page_size=" querystring parameter
    filter_backends = (
        # https://www.django-rest-framework.org/api-guide/filtering/#djangofilterbackend, https://django-filter.readthedocs.io/en/latest/index.html
        django_filters.DjangoFilterBackend,  # allows the use of filtersets (in filters.py); set filterset_class in the subclass
        # https://www.django-rest-framework.org/api-guide/filtering/#orderingfilter
        filters.OrderingFilter,     # ?ordering=...   ; requires an ordering_fields variable to be set in the class instance
        # https://www.django-rest-framework.org/api-guide/filtering/#searchfilter
        #filters.SearchFilter,      # ?search= ... ; requires a search_fields variable to be set in the class instance 
        CustomSearchFilter          # ?search= ... ; requires a search_fields variable to be set in the class instance 
        )
    # NB: the CustomSearchFilter normalizes search string by default; add "normalize=False" to the query to swith normalization off


    # in the subclass: define the following variables:
    # * queryset (either as queryset=<model>.objects.all() or by defining a custom get_queryset() function)
    # * serializer_class
    # and, optionally:
    # * search_fields      # list of fields the search query should search
    # * ordering_fields    # list of fields by which results can be sorted
    # * filterset_class    # custom filter class to be used (in filters.py)



@api_view(['GET'])
def api_overview(request):
    api_urls = {
        'List all authors in a specific release:': '<release_code>/author/all/ e.g., `2022.1.6/author/all/`',
        'List all texts in a specific release:': '<release_code>/text/all/ e.g., `2022.1.6/text/all/`',
        'List all text versions in a specific release:': '<release_code>/version/all/ e.g., `2022.1.6/version/all/`',
        '-----------------------------------------------':'-----------------------------------------------',
        'Get a single author by their URI:': '<release_code>/author/<str:author_uri>/ e.g. `2022.1.6/author/0179MalikIbnAnas/`',
        'Get a text by its URI:': '<release_code>/text/<str:text_uri>/ e.g. `2022.1.6/text/0179MalikIbnAnas.Muwatta/`',
        'Get a text version by its URI:': '<release_code>/version/<str:version_code>/ e.g. `2022.1.6/version/JK000466/`',
        '----------------------------------------------':'------------------------------------------------',
        'Get text reuse statistics for a specific pair of texts:': '<release_code>/text-reuse-stats/<str:book1>_<str:book1>/ e.g. `2022.1.6/text-reuse-stats/JK000466_Shamela0009783BK1/`',
        'Get all statistics for texts that have text reuse in common with a specific text:': '<release_code>/text-reuse-stats/<str:version_code>/ e.g. `2022.1.6/text-reuse-stats/JK000466/`',
        'Get all pairwise text reuse statistics:': '<release_code>/text-reuse-stats/all/ e.g. `2022.1.6/text-reuse-stats/all/`',
        '------------------------------------------------':'-----------------------------------------------',
        'Get statistics about a corpus release': '<release_code>/corpusinsights/  e.g., `2022.1.6/corpusinsights/`',
        'Get information on a specific release of the OpenITI corpus': '<release_code>/release-info  e.g. `2022.1.6/release-info`',
        '--------------------------------------------':'-----------------------------------------------',
        'Search authors:': '<release_code>/author/all/?search= e.g., `2022.1.6/author/all/?search=الجاحظ 255`',
        'Search texts:': '<release_code>/text/all/?search= e.g., `2022.1.6/text/all/?search=الجاحظ Hayawan`',
        'Search text versions:': '<release_code>/version/all/?search= e.g., `2022.1.6/version/all/?search=الجاحظ Hayawan pri`',
        '-------------------------------------------------':'-----------------------------------------------',
        'Filter authors based on a specific field:': '<release_code>/author/?author_lat= e.g., `2022.1.6/author/?author_lat=Jahiz`',
        'Filter texts based on a specific field:': '<release_code>/text/?author_ar= e.g., `2022.1.6author/?author_lat=الجاحظ`',    
        '-----------------------------------------------------':'-----------------------------------------------',
        'Get a list of all sources for our texts': 'source-collection/all/', 
        'Get a list of all relation types in the database': 'relation-type/all/', 
        'Get a list of all relations (between persons, books, places) in the database': 'relation/all/',
        'Get a list of all manually entered person names in the database': 'person-name/all/', 

    }

    return Response(api_urls)



@api_view(['GET'])
def get_text(request, text_uri, release_code=None):
    """Get a single text by its URI (additionally, a release code)"""
    try:
        if release_code:
            text = Text.objects\
                .filter(text_uri=text_uri, version__release_version__release_info__release_code=release_code)\
                .first()  # multiple (identical) results will be returned because of the join strategy; take the first one
        else:
            text = Text.objects.get(text_uri=text_uri)
        serializer = TextSerializer(text, many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404




@api_view(['GET'])
def get_version(request, version_code, release_code=None):
    """Get a text version by its version_code (and, if provided, release_code)"""

    # if user provided a full version URI, extract the version_code
    if "-" in version_code: 
        version_code = version_code.split("-")[0].split(".")[-1]

    try:
        if release_code:
            version = Version.objects\
                .filter(version_code=version_code, 
                        release_version__release_info__release_code=release_code)\
                .first()  # multiple (identical) results will be returned because of the join strategy; take the first one
            serializer = VersionSerializer(
                version,
                many=False,
                context=dict(release_code=release_code)  # pass the release code to the serializer
            )
        else:
            version = Version.objects.get(version_code=version_code)
            serializer = VersionSerializer(version, many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404


@api_view(['GET'])
def get_author(request, author_uri, release_code=None):
    """Get an author record by its author_uri (and, if provided, release_code)"""
    try:
        if release_code:
            author = Author.objects\
                .filter(author_uri=author_uri, text__version__release_version__release_info__release_code=release_code)\
                .first() # multiple (identical) results will be returned because of the join strategy; take the first one
        else:
            author = Author.objects.get(author_uri=author_uri)
        serializer = AuthorSerializer(author, many=False)
        return Response(serializer.data)
        
    except Exception as e:
        print("get_author failed:")
        print(e)
        raise Http404


@api_view(['GET'])
def get_corpus_insights(request, release_code=None):
    """Get some aggregated stats on the corpus (number of authors, texts, ...)"""
    try:
        if release_code:
            corpus_insight_stats = CorpusInsights.objects.get(release_info__release_code=release_code)
            serializer = CorpusInsightsSerializer(corpus_insight_stats, many=False)
        else:
            corpus_insight_stats = CorpusInsights.objects.all()
            serializer = CorpusInsightsSerializer(corpus_insight_stats, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        print("get_corpus_insights failed:")
        print(e)
        raise Http404

    return Response(serializer.data)








#class AuthorListView(generics.ListAPIView):
class AuthorListView(CustomListView):
    """
    Return a paginated list of author metadata objects
    (each containing metadata on an author, their texts and versions of their texts)

    Filter, sort and search are enabled, and fields can be selected.

    Examples: 
        /author/all/
        /author/all/?fields=author_uri,texts   # get only these two fields!
        /author/all/?search=طبري
        /author/all/?ordering=author_uri
        /author/all/?page=2
        /author/all/?page_size=100     # default: 10, max: 200
        /author/all/?fields=author_uri,texts&search=تاريخ&page=2   # TO DO: fix search Error: "Related Field got invalid lookup: icontains"
    """
    serializer_class = AuthorSerializer

    # customize the search:
    search_fields = [field.name for field in Author._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__" + field.name for field in Text._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__version__" + field.name for field in Version._meta.get_fields() if (field.name not in excl_flds)] \
        + ["name_element__" + field.name for field in PersonName._meta.get_fields()
           if (field.name not in excl_flds)]
    search_fields = (search_fields)

    # Customize filtering:
    filterset_class = AuthorFilter

    def get_queryset(self):
        """Filter the author objects present in the specified release, 
        if a release_code was specified in the URL"""
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        if release_code:
            queryset = Author.objects\
                .filter(text__version__release_version__release_info__release_code=release_code)\
                .distinct()
        else:
            queryset = Author.objects.all()

        # Create a list of all valid filters to validate the request:
        # 1. get all filters defined in the body of the filter class: 
        declared_filters = list(self.filterset_class.declared_filters.keys())  
        # 2. get all fields listed for exact lookup in the filter class' Meta class:
        declared_filters += list(self.filterset_class.get_fields().keys())     
        #print(dir(self.filterset_class))  # gets you a list of all available properties of the filterset_class
        # 3. add the default allowed parameters (like search, page, fields, ...):
        all_allowed_parameters = allowed_parameters + declared_filters
        # # 3. create an additional filter "__in" for each declared filter; this allows "OR" filtering:
        # declared_filters_in = [f+"__in" for f in declared_filters]
        # # 4. add the default allowed parameters (like search, page, fields, ...):
        # all_allowed_parameters = allowed_parameters + declared_filters + declared_filters_in

        # Now check all elements in the query URL to check if they are valid:
        for p in self.request.GET:
            if p not in all_allowed_parameters:
                msg = {"message": "Invalid parameter: "+ p}
                res = serializers.ValidationError(msg)
                res.status_code=200
                raise res

        return queryset



# class VersionListView(generics.ListAPIView):
class VersionListView(CustomListView):
    """Display the version objects in the database as a paginated list.

    Filter, sort and search are enabled, and fields can be selected.

    Examples: 
        /version/all/
        /version/all/?fields=version_uri
        /version/all/?search=JK000001
        /version/all/?ordering=version_uri
        /version/all/?page=2
        /version/all/?page_size=100     # default: 10, max: 200
        /version/all/?fields=book_id&search=JK000001&page=2
    
    """

    serializer_class = VersionSerializer

    # define the default search fields - these may be overridden 
    # by using the "&search_fields" switch in the query string 
    # (as defined in the VersionSearchFilter)
    search_fields = [
        "version_uri",        # also contains the version_code, source_coll__code, text_uri, author_uri and text__author__date_str!
        "text__titles_ar", "text__titles_lat", # contain all attested titles in a single string
        "text__author__author_ar", "text__author__author_lat", # contains all attested author names (incl. from the name elements)
        "release_version__analysis_priority", "release_version__annotation_status", 
        ]

    filter_backends = (django_filters.DjangoFilterBackend,
                       VersionSearchFilter, #filters.SearchFilter, 
                       filters.OrderingFilter)
    filterset_class = VersionFilter

    ordering_fields = ['text__titles_lat', 'text__titles_ar',
                       "text__author__date", 'tok_length']
    ordering_fields = (ordering_fields)

    def get_serializer_context(self):
        """Send the release code to the serializer
        
        See https://stackoverflow.com/a/38723709/4045481"""
        context = super().get_serializer_context()
        try: 
            release_code = self.kwargs['release_code']
        except:
            release_code = None
        context["release_code"] = release_code
        return context

    def get_queryset(self):
        """Get the queryset, based on whether or not
        the version_code is defined in the URL"""

        # Create a list of all valid filters to validate the request:
        # 1. get all filters defined in the body of the filter class: 
        declared_filters = list(self.filterset_class.declared_filters.keys())  
        # 2. get all fields listed for exact lookup in the filter class' Meta class:
        declared_filters += list(self.filterset_class.get_fields().keys())     
        #print(dir(self.filterset_class))  # gets you a list of all available properties of the filterset_class
        # 3. add the default allowed parameters (like search, page, fields, ...):
        all_allowed_parameters = allowed_parameters + declared_filters
        # # 3. create an additional filter "__in" for each declared filter; this allows "OR" filtering:
        # declared_filters_in = [f+"__in" for f in declared_filters]
        # # 4. add the default allowed parameters (like search, page, fields, ...):
        # all_allowed_parameters = allowed_parameters + declared_filters + declared_filters_in

        # Now check all elements in the query URL to check if they are valid:
        for p in self.request.GET:
            if p not in all_allowed_parameters:
                msg = {"message": "Invalid parameter "+ p}
                res = serializers.ValidationError(msg)
                res.status_code=200
                raise res
            else:
                print(p, ": parameter allowed")

        # # get the release and version code from the URL:
        # try:
        #     release_code = self.kwargs['release_code']
        # except: 
        #     release_code = None
        # try:
        #     version_code = self.kwargs['version_code']
        # except:
        #     version_code = None
        # # filter the version objects based on release and version codes:
        # if release_code:
        #     if version_code: # this will in fact be handled by the get_release_version function
        #         queryset = Version.objects\
        #             .filter(version_code=version_code, release_version__release_info__release_code=release_code)\
        #             .distinct()
        #     else: # this will now in fact be handled by the ReleaseVersionListView
        #         queryset = Version.objects\
        #             .prefetch_related("release_versions__release_info")\
        #             .filter(release_version__release_info__release_code=release_code)\
        #             .distinct()
        #         print(queryset)
        # else:
        #     if version_code:
        #         queryset = Version.objects\
        #             .filter(version_code=version_code)\
        #             .distinct()
        #     else:
        #         queryset = Version.objects.all()
 
        # get the release code from the URL:
        try:
            version_code = self.kwargs['version_code']
        except:
            version_code = None
        # filter the version objects based on the version_code:
        if version_code:
            queryset = Version.objects\
                .filter(version_code=version_code)\
                .distinct()
        else:
            queryset = Version.objects.all()

        return queryset


#class TextListView(generics.ListAPIView):
class TextListView(CustomListView):
    """
    Display the Text objects as a paginated list.

    Filter, sort and search are enabled, and fields can be selected.

    Examples: 
        /text/all/
        /text/all/?fields=text_uri,titles_ar   # get only these two fields!
        /text/all/?search=JK000001
        /text/all/?ordering=text_uri
        /text/all/?page=2
        /text/all/?page_size=100     # default: 10, max: 200
        /text/all/?fields=text_uri&search=JK000001&page=2
    """
    # Define the fields that will be searched when user uses "search=" query parameter
    # TO DO: review the search_fields
    search_fields = [field.name for field in Text._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author__" + field.name for field in Author._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author__name_element__" + field.name for field in PersonName._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version__" + field.name for field in Version._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version__version__" + field.name for field in ReleaseVersion._meta.get_fields() if (field.name not in excl_flds)]

    # define the fields the user can sort the results by (using "ordering=" query parameter)
    ordering_fields = ['text_uri']
    ordering_fields = (ordering_fields)

    # define how the results should be represented in json format:
    serializer_class = TextSerializer

    # define the ways the results can be filtered:
    filterset_class = TextFilter


    def get_queryset(self):
        """Filter the text objects that are in a specific release
        (if a release code is provided in the query URL)"""

        # Create a list of all valid filters to validate the request:
        # 1. get all filters defined in the body of the filter class: 
        declared_filters = list(self.filterset_class.declared_filters.keys())  
        # 2. get all fields listed for exact lookup in the filter class' Meta class:
        declared_filters += list(self.filterset_class.get_fields().keys())     
        #print(dir(self.filterset_class))  # gets you a list of all available properties of the filterset_class
        # 3. add the default allowed parameters (like search, page, fields, ...):
        all_allowed_parameters = allowed_parameters + declared_filters
        # # 3. create an additional filter "__in" for each declared filter; this allows "OR" filtering:
        # declared_filters_in = [f+"__in" for f in declared_filters]
        # # 4. add the default allowed parameters (like search, page, fields, ...):
        # all_allowed_parameters = allowed_parameters + declared_filters + declared_filters_in

        # Now check all elements in the query URL to check if they are valid:
        for p in self.request.GET:
            if p not in all_allowed_parameters:
                msg = {"message": "Invalid parameter "+ p}
                res = serializers.ValidationError(msg)
                res.status_code=200
                raise res
            else:
                print(p, ": parameter allowed")

        # check if the URL contains a release code:
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        # filter the text objects related to the release: 
        if release_code:
            queryset = Text.objects\
                .filter(version__release_version__release_info__release_code=release_code)\
                .distinct()  # if using all, we get the number of rows for the joined table (all identical)!
        else:
            queryset = Text.objects.all()

        return queryset


#class PersonNameListView(generics.ListAPIView):
class PersonNameListView(CustomListView):
    """Display all person names (independent of releases) in a paginated list."""
    queryset = PersonName.objects.all()
    serializer_class = PersonNameSerializer

#class RelationsListView(generics.ListAPIView):
class RelationsListView(CustomListView):
    """Get all relations in the A2BRelations model (independent of releases) in a paginated list."""
    queryset = A2BRelation.objects.all()
    serializer_class = AllRelationsSerializer


#class RelationTypesListView(generics.ListAPIView):
class RelationTypesListView(CustomListView):
    """Get all relation types in the database (independent of releases) in a paginated list."""
    queryset = RelationType.objects.all()
    serializer_class = AllRelationTypesSerializer

@api_view(['GET'])
def get_relation_type(request, code):
    """Get the text reuse statistics for a pair of texts."""
    
    try:
        rel = RelationType.objects.get(code=code)
        print(rel)
        serializer = AllRelationTypesSerializer(rel, many=False)
        
        return Response(serializer.data)  
    except RelationType.DoesNotExist:
        raise Http404


#class TextReuseStatsListView(generics.ListAPIView):
class TextReuseStatsListView(CustomListView):
    """Get all text reuse stats for a specific release or all releases as a paginated list
    (including selected metadata for book 1 and book 2)"""

    # define the way the json output will look:
    serializer_class = ShallowTextReuseStatsSerializer
    
    # allow filtering using query parameters (e.g., ?book_1=Tabari.Tarikh )
    filterset_class = TextReuseFilter

    # allow sorting using a query parameter (e.g., ?ordering=instances_count ) 
    ordering_fields = ['instances_count', 'book1_words_matched', 'book2_words_matched', 
                       'book1_pct_words_matched', 'book2_pct_words_matched',
                       'book_1__version__version_uri', 'book_2__version__version_uri']
    ordering_fields = (ordering_fields)

    # allow searching these fields using ?search= paramater
    search_fields = ["book_1__version__text__author__author_ar", 
                     "book_2__version__text__author__author_ar", 
                     "book_1__version__text__author__author_lat", 
                     "book_2__version__text__author__author_lat", 
                     "book_1__version__text__titles_ar", 
                     "book_2__version__text__titles_lat",
                     "book_1__version__text__titles_ar", 
                     "book_2__version__text__titles_lat", 
                     "book_1__version__version_uri", 
                     "book_2__version__version_uri"]

    def get_queryset(self):
        """Filter the queryset based on the release_code and/or book1 elements in the URL"""

        # Create a list of all valid filters to validate the request:
        # 1. get all filters defined in the body of the filter class: 
        declared_filters = list(self.filterset_class.declared_filters.keys())  
        # 2. get all fields listed for exact lookup in the filter class' Meta class:
        declared_filters += list(self.filterset_class.get_fields().keys())     
        #print(dir(self.filterset_class))  # gets you a list of all available properties of the filterset_class
        # 3. add the default allowed parameters (like search, page, fields, ...):
        all_allowed_parameters = allowed_parameters + declared_filters
        # # 3. create an additional filter "__in" for each declared filter; this allows "OR" filtering:
        # declared_filters_in = [f+"__in" for f in declared_filters]
        # # 4. add the default allowed parameters (like search, page, fields, ...):
        # all_allowed_parameters = allowed_parameters + declared_filters + declared_filters_in

        # Now check all elements in the query URL to check if they are valid:
        for p in self.request.GET:
            if p not in all_allowed_parameters:
                msg = {"message": "Invalid parameter "+ p}
                res = serializers.ValidationError(msg)
                res.status_code=200
                raise res
            else:
                print(p, ": parameter allowed")

        # check whether the URL contains a release_code:
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        # check whether the URL contains a book1 element:
        try:
            book1 = self.kwargs['book1']
        except: 
            book1 = None
        print("---", release_code, book1)

        # filter the TextReuseStats objects:
        if release_code:
            if book1:
                queryset = TextReuseStats.objects\
                    .select_related("release_info", "book_1")\
                    .filter(release_info__release_code=release_code, book_1__version__version_uri__contains=book1)\
                    .distinct()
            else:
                queryset = TextReuseStats.objects\
                    .select_related("release_info")\
                    .filter(release_info__release_code=release_code)\
                    .distinct()
        else:
            if book1:
                print("book1:", book1)
                queryset = TextReuseStats.objects\
                    .select_related("book_1")\
                    .filter(book_1__version__version_uri__contains=book1)\
                    .distinct()
            else:
                print("book1 nor release defined")
                queryset = TextReuseStats.objects.all()

        return queryset

class TextReuseStatsB1ListView(TextReuseStatsListView):
    """Get all text reuse stats for book1 (include only metadata for book 2)"""
    # NB: this view class inherits its get_queryset() and filters from TextReuseStatsListView
    serializer_class = TextReuseStatsSerializerB1


@api_view(['GET'])
def get_pair_text_reuse_stats(request, book1, book2, release_code=None):
    """Get the text reuse statistics for a pair of texts."""
    try:
        if release_code:
            stats = TextReuseStats.objects.get(book_1__version__version_uri__contains=book1, 
                                               book_2__version__version_uri__contains=book2, 
                                               release_info__release_code=release_code)
            serializer = ShallowTextReuseStatsSerializer(stats, many=False)
        else:
            stats = TextReuseStats.objects.filter(book_1__version__version_uri__contains=book1, 
                                                  book_2__version__version_uri__contains=book2)
            serializer = ShallowTextReuseStatsSerializer(stats, many=True)
        
        return Response(serializer.data)  
    except TextReuseStats.DoesNotExist:
        raise Http404


#class ReleaseVersionListView(generics.ListAPIView):
class ReleaseVersionListView(CustomListView):
    """Display the  release version objects in the database as a paginated list.

    Filter, sort and search are enabled, and fields can be selected.

    Examples: 
        /version/all/
        /version/all/?fields=version_uri
        /version/all/?search=JK000001
        /version/all/?ordering=version_uri
        /version/all/?page=2
        /version/all/?page_size=100     # default: 10, max: 200
        /version/all/?fields=book_id&search=JK000001&page=2
    """

    search_fields = [
        'analysis_priority', 'annotation_status',
        'version__version_uri',        # also contains the version_code, source_coll__code, text_uri, author_uri and text__author__date_str!
        "version__text__titles_ar", "version__text__titles_lat", # contain all attested titles in a single string
        "version__text__author__author_ar", "version__text__author__author_lat", # contains all attested author names (incl. from the name elements)
        ]



    filter_backends = (django_filters.DjangoFilterBackend,
                       ReleaseVersionSearchFilter, 
                       filters.OrderingFilter) 

    serializer_class = ReleaseVersionSerializer

    filterset_class = ReleaseVersionFilter

    ordering_fields = ['tok_length', 'analysis_priority', 'version__text__author__date', 
                       'version__text__title_lat_prefered', 'version__text__author__author_lat_prefered',
                       'versionwise_reuse__n_instances']

    def get_queryset(self):
        """Filter the ReleaseVersion objects, based on the release_code in the query URL"""

        # Create a list of all valid filters to validate the request:
        # 1. get all filters defined in the body of the filter class: 
        declared_filters = list(self.filterset_class.declared_filters.keys())  
        # 2. get all fields listed for exact lookup in the filter class' Meta class:
        declared_filters += list(self.filterset_class.get_fields().keys())     
        #print(dir(self.filterset_class))  # gets you a list of all available properties of the filterset_class
        # 3. add the default allowed parameters (like search, page, fields, ...):
        all_allowed_parameters = allowed_parameters + declared_filters
        # # 3. create an additional filter "__in" for each declared filter; this allows "OR" filtering:
        # declared_filters_in = [f+"__in" for f in declared_filters]
        # # 4. add the default allowed parameters (like search, page, fields, ...):
        # all_allowed_parameters = allowed_parameters + declared_filters + declared_filters_in
        

        # Now check all elements in the query URL to check if they are valid:
        for p in self.request.GET:
            if p not in all_allowed_parameters:
                msg = {"message": "Invalid parameter: "+ p}
                res = serializers.ValidationError(msg)
                res.status_code=200
                raise res

        # get the release code from the URL:
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        # filter the ReleaseVersion objects based on the release code:
        if release_code:
            queryset = ReleaseVersion.objects\
                .filter(release_info__release_code=release_code)\
                .distinct()
        else:
            queryset = ReleaseVersion.objects.all()

        return queryset


#class GetReleaseInfoList(generics.ListAPIView):
class GetReleaseInfoList(CustomListView):
    queryset = ReleaseInfo.objects.all()
    serializer_class = ReleaseInfoSerializer


@api_view(['GET'])
def get_release_info(request, release_code):
    """Get info on a release."""
    try:
        release_info = ReleaseInfo.objects.get(release_code=release_code)
        serializer = ReleaseInfoSerializer(release_info, many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404
    
#class GetSourceCollectionDetailsList(generics.ListAPIView):
class GetSourceCollectionDetailsList(CustomListView):
    queryset = SourceCollectionDetails.objects.all()
    serializer_class = SourceCollectionDetailsSerializer


@api_view(['GET'])
def get_source_collection(request, code):
    """Get info on a release."""
    try:
        coll = SourceCollectionDetails.objects.get(code=code)
        serializer = SourceCollectionDetailsSerializer(coll, many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404


#class GitHubIssuesListView(generics.ListAPIView):
class GitHubIssuesListView(CustomListView):
    """
    Return a paginated list of GitHub Issues
    """
    queryset = GitHubIssue.objects.all()
    serializer_class = GitHubIssueSerializer



#########################  UNUSED FUNCTIONS  #############################################


# @api_view(['GET'])
# def get_release_text(request, release_code, text_uri):
#     """Get a text version by its version_code and release_code"""

#     try:
#         text = Text.objects.filter(text_uri=text_uri, version__release_version__release_info__release_code=release_code).first()
#         serializer = TextSerializer(text, many=False)
#         return Response(serializer.data)
#     except Text.DoesNotExist:
#         raise Http404



# # Remove this before going live as we shouldn't allow any POST method
# @api_view(['POST'])
# def book_create(request):
#     serializer = VersionSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# # Not in use but useful if we want everything in one go
# @api_view(['GET'])
# def book_list(request):
#     books = Version.objects.all()
#     serializer = VersionSerializer(books, many=True)
#     return Response(serializer.data)


@api_view(['GET'])
def get_release_version(request, version_code, release_code=None):
    """Get a single release version by its version_code and release_code
    """

    # if user provided a full version URI, extract the version_code
    if "-" in version_code: 
        version_code = version_code.split("-")[0].split(".")[-1]

    try:
        if release_code:
            release_version = ReleaseVersion.objects\
                .get(version__version_code=version_code,
                     release_info__release_code=release_code)
            serializer = ReleaseVersionSerializer(
                release_version,
                many=False,
                context=dict(release_code=release_code)  # pass the release code to the serializer
            )
        else:
            release_version = ReleaseVersion.objects.get(release_info__release_code=release_code, version__version_code=version_code)
            serializer = ReleaseVersionSerializer(
                release_version, 
                many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404
    