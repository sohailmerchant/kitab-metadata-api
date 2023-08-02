from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404

from rest_framework import generics, status
from rest_framework import pagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as django_filters
from rest_framework import filters


from .models import Author, PersonName, Text, Version, CorpusInsights, TextReuseStats, A2BRelation, ReleaseVersion, SourceCollectionDetails, ReleaseInfo, RelationType
from .serializers import TextSerializer, VersionSerializer, PersonNameSerializer, ReleaseVersionSerializer, AuthorSerializer, TextReuseStatsSerializer, CorpusInsightsSerializer, AllRelationSerializer,  SourceCollectionDetailsSerializer, ReleaseInfoSerializer, ShallowTextReuseStatsSerializer, TextReuseStatsSerializerB1, AllRelationTypesSerializer#, RelationTypeSerializer
from .filters import AuthorFilter, VersionFilter, TextFilter, TextReuseFilter, ReleaseVersionFilter


    # path('all-releases/version/all/', views.ReleaseVersionListView.as_view(), name='all-releases-all-versions'),
    # path('all-releases/version/', views.ReleaseVersionListView.as_view(), name='all-releases-all-versions'),
    # #path('all-releases/version/<str:version_code>/', views.ReleaseVersionListView.as_view(), name='all-releases-one-version'), # multiple results possible!
    # path('all-releases/version/<str:version_code>/', views.get_version, name='all-releases-one-version'),
    
    # path('<str:release_code>/version/all/', views.ReleaseVersionListView.as_view(), name='one-release-all-versions'),
    # path('<str:release_code>/version/', views.ReleaseVersionListView.as_view(), name='one-release-all-versions'),
    # path('<str:release_code>/version/<str:version_code>/', views.get_release_version, name='one-release-one-version'),

    # # text endpoints:  # TO DO: use other view for the texts

    # path('all-releases/text/', views.TextListView.as_view(), name='all-releases-all-texts'),
    # path('all-releases/text/all/', views.TextListView.as_view(), name='all-releases-all-texts'),
    # path('all-releases/text/<str:text_uri>/', views.get_text, name='all-releases-one-text'),

    # path('<str:release_code>/text/', views.TextListView.as_view(), name='one-release-all-texts'),
    # path('<str:release_code>/text/all/', views.TextListView.as_view(), name='one-release-all-texts'),
    # path('<str:release_code>/text/<str:text_uri>/', views.get_text, name='one-release-one-text'),

    # # author endpoints:

    # path('all-releases/author/', views.AuthorListView.as_view(), name='all-releases-all-authors'),
    # path('all-releases/author/all/', views.AuthorListView.as_view(), name='all-releases-all-authors'),
    # path('all-releases/author/<str:author_uri>/', views.get_author, name='all-releases-one-author'),

    # path('<str:release_code>/author/', views.AuthorListView.as_view(), name='one-release-all-authors'),
    # path('<str:release_code>/author/all/', views.AuthorListView.as_view(), name='one-release-all-authors'),
    # path('<str:release_code>/author/<str:author_uri>/', views.get_author, name='one-release-one-author'),

    # # release info endpoints:

    # path('all-releases/release-details/', views.GetReleaseInfoList.as_view(), name='release-details-all'),
    # path('<str:release_code>/release-details/', views.get_release_info, name='release-details'),

    # # A2BRelations endpoints (independent of releases):

    # path('all-releases/relation/all/', views.RelationsListView.as_view(), name='all-releases-relations'),
    # path('all-releases/relation/', views.RelationsListView.as_view(), name='all-releases-relations'),

    # # source collections info (independent of releases):

    # path('source-collections/all/', views.GetSourceCollectionDetailsList.as_view(), name='source-collections'),
    # path('source-collections/', views.GetSourceCollectionDetailsList.as_view(), name='source-collections'),
    # path('source-collections/<str:code>', views.GetSourceCollectionDetailsList.as_view(), name='source-collections'),

    # # corpus insights (statistics on the number of books, largest book, etc. for each release):
    
    # path('all-releases/corpusinsights/', views.get_corpus_insights, name='corpusinsights'),
    # path('<str:release_code>/corpusinsights/', views.get_corpus_insights, name='corpusinsights'),

    # # Text reuse statistics:

    # path('all-releases/text-reuse-stats/<str:book1>_<str:book2>/', views.get_pair_text_reuse_stats, name='text-reuse-pair'),
    # path('all-releases/text-reuse-stats/all/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),
    # path('all-releases/text-reuse-stats/<str:book1>/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),

    # path('<str:release_code>/text-reuse-stats/<str:book1>_<str:book2>/', views.get_pair_text_reuse_stats, name='text-reuse-pair'),
    # path('<str:release_code>/text-reuse-stats/all/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),
    # path('<str:release_code>/text-reuse-stats/<str:book1>/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),



@api_view(['GET'])
def api_overview(request):
    api_urls = {
        'List all text versions:': '<release_code>/version/all/ e.g., `2022.1.6/version/all/',
        'List all authors:': '<release_code>/author/all/',
        'List all texts:': '<release_code>/text/all/',

        'Get a text by its URI:': '<release_code>/text/<str:text_uri>/ e.g. `2022.1.6/text/0179MalikIbnAnas.Muwatta`',
        'Get an author by their URI:': '<release_code>/author/<str:author_uri>/ e.g. `2022.1.6/author/0179MalikIbnAnas`',

        'Search authors:': '<release_code>/author/all/author/?search= e.g., `2022.1.6/author/all/?search=الجاحظ 255`',
        'Search texts:': '<release_code>/text/all/?search= e.g., `2022.1.6text/all/?search=الجاحظ Hayawan`',
        'Search text versions:': '<release_code>/text/all/?search= e.g., `2022.1.6text/all/?search=الجاحظ Hayawan Shamela`',

        'Filter authors based on a specific field:': '<release_code>/author/?author_lat= e.g., `2022.1.6/author/?author_lat=Jahiz`',
        'Filter texts based on a specific field:': '<release_code>/text/?author_lat= e.g., `2022.1.6author/?author_lat=Jahiz`',

        'Get statistics about the corpus': '<release_code>/corpusinsights/',
        'Get pairwise text reuse data': '<release_code>/text-reuse-stats/'
    }



    return Response(api_urls)

# Not in use but useful if we want everything in one go
@api_view(['GET'])
def book_list(request):
    books = Version.objects.all()
    serializer = VersionSerializer(books, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_text(request, text_uri, release_code=None):
    """Get a single text by its URI (additionally, a release code"""
    print("RELEASE_CODE:", release_code)

    try:
        if release_code:
            print(release_code)
            text = Text.objects\
                .filter(text_uri=text_uri, version__release_version__release_info__release_code=release_code)\
                .first()  # .distinct() not necessary: will all be the same
            print(text)
        else:
            print(release_code)
            text = Text.objects.get(text_uri=text_uri)
        serializer = TextSerializer(text, many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404



# @api_view(['GET'])
# def get_release_text(request, release_code, text_uri):
#     """Get a text version by its version_code and release_code"""

#     try:
#         text = Text.objects.filter(text_uri=text_uri, version__release_version__release_info__release_code=release_code).first()
#         serializer = TextSerializer(text, many=False)
#         return Response(serializer.data)
#     except Text.DoesNotExist:
#         raise Http404

# Get a text version by its version_code
@api_view(['GET'])
def get_version(request, version_code, release_code=None):
    if "-" in version_code:
        version_code = version_code.split("-")[0].split(".")[-1]
    print("VERSION_CODE:", version_code)
    print("RELEASE_CODE:", release_code)

    try:
        if release_code:
            version = Version.objects\
                .filter(version_code=version_code, release_version__release_info__release_code=release_code)\
                .distinct().first()
            print(version)
            serializer = VersionSerializer(version, many=False, context=dict(release_code=release_code))
        else:
            #version = Version.objects.prefetch_related("divisions", "part_of").get(version_code=version_code).all()
            version = Version.objects.get(version_code=version_code)
            serializer = VersionSerializer(version, many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404



@api_view(['GET'])
def get_release_version(request, version_code, release_code=None):
    """Get a text version by its version_code and release_code"""

    try:
        if release_code:
            release_version = ReleaseVersion.objects.get(release_info__release_code=release_code, version__version_code=version_code)
        else:
            release_version = ReleaseVersion.objects.get(release_info__release_code=release_code, version__version_code=version_code)
        serializer = ReleaseVersionSerializer(release_version, many=False)
        return Response(serializer.data)
    except Text.DoesNotExist:
        raise Http404
    

# Get an author record by its author_uri
@api_view(['GET'])
def get_author(request, author_uri, release_code=None):
    print("GETTING AUTHOR!")
    print(author_uri)
    print(release_code)

    try:
        if release_code:
            author = Author.objects\
                .filter(author_uri=author_uri, text__version__release_version__release_info__release_code=release_code)\
                .distinct().first()
            print(author)
        else:
            author = Author.objects.get(author_uri=author_uri)
        serializer = AuthorSerializer(author, many=False)
        return Response(serializer.data)
        
    except Exception as e:
        print("get_author failed:")
        print(e)
        raise Http404


# Get some aggregated stats on the corpus like authors no, book no. etc.
@api_view(['GET'])
def get_corpus_insights(request, release_code=None):
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


# Remove this before going live as we shouldn't allow any POST method
@api_view(['POST'])
def book_create(request):
    serializer = VersionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


'''' Get all books by pagination, filter and search enable. we can select fields also.
Example: /book/all/?fields=book_id or /book/all/?search=JK000001 or book/all/?fields=book_id&search=JK000001
'''


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 200
    last_page_strings = ('the_end',)

    def get_paginated_response(self, data):

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


# fields to be excluded from search (because they are not string fields):
# excl_flds = ["id", "date", "date_AH", "date_CE", "tok_length", "char_length",  # numeric fields
#             "text", "name_element", "version", "author", "version_code", "text"]      # foreign key fields
excl_flds = [
    # numeric fields:
    "id", "date", "date_AH", "date_CE", "tok_length", "char_length",
    # foreign key fields:
    "text", "name_element", "version", "author", "version_code", "text",
    "related_persons", "related_places", "related_texts", "place_relations",
    "person_a", "person_b", "text_a", "text_b",
    "place_a", "place_b", "relation_type", "parent_type",
    # related fields:
    'authormeta', 'textmeta', 'related_person_a', 'related_person_b',
    "related_text_a", "related_text_b"]


class AuthorListView(generics.ListAPIView):
    """
    Return a paginated list of author metadata objects
    (each containing metadata on an author, their texts and versions of their texts)
    """
    #queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = CustomPagination

    # customize the search:

    search_fields = [field.name for field in Author._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__" + field.name for field in Text._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__version__" + field.name for field in Version._meta.get_fields() if (field.name not in excl_flds)] \
        + ["name_element__" + field.name for field in PersonName._meta.get_fields()
           if (field.name not in excl_flds)]
    # print("AUTHOR SEARCH FIELDS:")
    # print(search_fields)

    # NB: excl_flds needs to be declared outside of the class for the list comprehension to work,
    # otherwise you get a NameError; see https://stackoverflow.com/a/13913933
    # print()
    # print("Search fields:")
    # print(search_fields)
    # print()
    search_fields = (search_fields)

    # Customize filtering:

    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = AuthorFilter

    # old experiments with filters by Sohail:

    # filter_fields ={
    #     #'annotation_status': ['in', 'exact'], # note the 'in'
    #     'text__text_uri': ['exact'],
    #     'text__titles_ar':['exact'] ,
    #     'text__titles_lat':['exact'],
    #     'text__version__version_code':['exact']
    # }

    # print(filter_fields)
    #filter_fields = ['titles_lat', 'book_id', 'titles_ar', 'annotation_status']
    # filter_fields = (filter_fields)
    #ordering_fields = ['titles_lat', 'titles_ar']
    #ordering_fields = (ordering_fields)

    def get_queryset(self):
        """Get the queryset, based on arguments provided in the URL"""
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
        return queryset


class VersionListView(generics.ListAPIView):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    pagination_class = CustomPagination

    # search_fields = [field.name for field in Author._meta.get_fields() if(field.name not in ["text","author_names", 'date', 'date_AH', 'date_CE', 'id'])]+ \
    #["version__"+ field.name for field in Text._meta.get_fields() if(field.name not in ["version","id", 'Author'])]\
    #+ ["text__version__"+ field.name for field in Version._meta.get_fields() if(field.name not in ["id", 'Text','tok_length','char_length'])]\
    #+ ["author_names__"+ field.name for field in PersonName._meta.get_fields() if(field.name not in ["id", 'Author'])]
    #print("FIELD", Version._meta.get_fields())
    search_fields = [field.name for field in Version._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__" + field.name for field in Text._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__author__" + field.name for field in Author._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__author__name_element__" + field.name for field in PersonName._meta.get_fields() if (field.name not in excl_flds)] \
        + ["release_version__" + field.name for field in ReleaseVersion._meta.get_fields() if (field.name not in excl_flds)] \

    # print("VERSION SEARCH FIELDS:")
    # print(search_fields)

    # Customize filtering:

    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
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
        """Get the queryset, based on arguments provided in the URL"""
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        try:
            version_code = self.kwargs['version_code']
        except:
            version_code = None
        print("VERSION_CODE:", version_code)
        if release_code:
            queryset = Version.objects\
                .filter(release_version__release_info__release_code=release_code)\
                .distinct()
        else:
            if version_code:
                queryset = Version.objects\
                    .filter(version_code=version_code)\
                    .distinct()
            else:
                queryset = Version.objects.all()
        return queryset


class TextListView(generics.ListAPIView):
    #queryset = Text.objects.all()
    #filter_fields = ['titles_lat', 'book_id', 'titles_ar', 'annotation_status']
    search_fields = [field.name for field in Text._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author__" + field.name for field in Author._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author__name_element__" + field.name for field in PersonName._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version__" + field.name for field in Version._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version__version__" + field.name for field in ReleaseVersion._meta.get_fields() if (field.name not in excl_flds)]

    # print(search_fields)

    #ordering_fields = ['titles_lat', 'titles_ar']
    serializer_class = TextSerializer
    pagination_class = CustomPagination
    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = TextFilter
    #filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    # search_fields = (search_fields)
    # filter_fields = (search_fields)
    #ordering_fields = (ordering_fields)

    def get_queryset(self):
        """Get the queryset, based on arguments provided in the URL"""
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        if release_code:
            queryset = Text.objects\
                .filter(version__release_version__release_info__release_code=release_code)\
                .distinct()  # if using all, we get the number of rows for the joined table!
        else:
            queryset = Text.objects.all()
        return queryset


class PersonNameListView(generics.ListAPIView):
    """Get all relations in the A2BRelations model (independent of releases)"""
    queryset = PersonName.objects.all()
    # for q in queryset:
    #    print(q.text_a)
    serializer_class = PersonNameSerializer

class RelationsListView(generics.ListAPIView):
    """Get all relations in the A2BRelations model (independent of releases)"""
    queryset = A2BRelation.objects.all()
    pagination_class = CustomPagination
    # for q in queryset:
    #    print(q.text_a)
    serializer_class = AllRelationSerializer


class RelationTypesListView(generics.ListAPIView):
    """Get all relation types in the database (independent of releases)"""
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
    except TextReuseStats.DoesNotExist:
        raise Http404


class GetAllTextReuseStats(generics.ListAPIView):
    """Get all text reuse stats for a specific release or all releases 
    (include selected metadata for book 1 and book 2)"""

    serializer_class = ShallowTextReuseStatsSerializer
    pagination_class = CustomPagination

    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    
    # allow additional query parameters like ?book_1=Tabari.Tarikh
    filterset_class = TextReuseFilter

    # allow additional query parameters like ?ordering=instances_count
    ordering_fields = ['instances_count', 'book1_word_match', 'book2_word_match']
    ordering_fields = (ordering_fields)

    # allow searching these fields using ?search=
    search_fields = ["book_1__version__text__author__author_ar", 
                     "book_2__version__text__author__author_ar", 
                     "book_1__version__text__titles_ar", 
                     "book_2__version__text__titles_ar", 
                     "book_1__version__version_uri", 
                     "book_2__version__version_uri"]

    def get_queryset(self):
        """Get the queryset, based on arguments provided in the URL"""
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        try:
            book1 = self.kwargs['book1']
        except: 
            book1 = None
        print("---", release_code, book1)
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

class GetAllTextReuseStatsB1(GetAllTextReuseStats):
    """Get all text reuse stats for book1 (include only metadata for book 2)"""
    # NB: this view class inherits its get_queryset() and filters from GetAllTextReuseStats
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


class ReleaseVersionListView(generics.ListAPIView):
    
    search_fields = [field.name for field in ReleaseVersion._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version__" + field.name for field in Version._meta.get_fields() if (field.name not in excl_flds)] 
        # + ["version__text__" + field.name for field in Text._meta.get_fields() if (field.name not in excl_flds)] \
        # + ["version__text__author__" + field.name for field in Author._meta.get_fields() if (field.name not in excl_flds)] \
        # + ["version__text__author__name_element__" +
        #     field.name for field in PersonName._meta.get_fields() if (field.name not in excl_flds)]

         ## had to put the list manualy as above function add these two field which makes the code 'version_uri', 'version_uri__release' 
    search_fields = ['release_info__release_code', 'url', 'analysis_priority', 'annotation_status', 'version__version_uri',  
                     'version__editor', 'version__edition_place', 'version__publisher', 'version__edition_date', 
                     'version__ed_info', 'version__language', 'version__release_version__tags', 'notes', 
                     'analysis_priority', 'annotation_status', 'version__text__text_uri', 
                     'version__text__titles_ar', 'version__text__titles_lat', 
                     'version__text__title_ar_prefered', 'version__text__title_lat_prefered', 
                     'version__text__text_type', 'version__text__tags', 'version__text__notes', 
                     'version__text__author__author_uri', 
                     'version__text__author__author_ar', 'version__text__author__author_lat', 
                     'version__text__author__author_ar_prefered', 'version__text__author__author_lat_prefered', 
                     'version__text__author__date_str', 'version__text__author__notes', 
                     'version__text__author__name_element__language', 
                     'version__text__author__name_element__shuhra', 'version__text__author__name_element__nasab', 
                     'version__text__author__name_element__kunya', 'version__text__author__name_element__ism', 
                     'version__text__author__name_element__laqab', 'version__text__author__name_element__nisba']

    
    # print("RELEASE SEARCH FIELDS:")
    # print(search_fields)

    serializer_class = ReleaseVersionSerializer
    pagination_class = CustomPagination

    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = ReleaseVersionFilter

    ordering_fields = ['tok_length', 'analysis_priority', 'version__text__author__date', 
                       'version__text__title_lat_prefered', 'version__text__author__author_lat_prefered']

    def get_queryset(self):
        """Get the queryset, based on arguments provided in the URL"""
        try:
            release_code = self.kwargs['release_code']
        except: 
            release_code = None
        if release_code:
            queryset = ReleaseVersion.objects\
                .filter(release_info__release_code=release_code)\
                .distinct()
        else:
            queryset = ReleaseVersion.objects.all()
        return queryset


class GetReleaseInfoList(generics.ListAPIView):

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
    
class GetSourceCollectionDetailsList(generics.ListAPIView):

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


