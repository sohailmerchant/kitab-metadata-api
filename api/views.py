from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404

from rest_framework import generics, status
from rest_framework import pagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as django_filters
from rest_framework import filters


from .models import authorMeta, personName, textMeta, versionMeta, CorpusInsights, TextReuseStats, a2bRelation, ReleaseMeta, SourceCollectionDetails, ReleaseDetails
from .serializers import TextSerializer, VersionMetaSerializer, PersonNameSerializer, ReleaseMetaSerializer, AuthorMetaSerializer, TextReuseStatsSerializer, CorpusInsightsSerializer, AllRelationSerializer,  SourceCollectionDetailsSerializer, ReleaseDetailsSerializer, ShallowTextReuseStatsSerializer
from .filters import authorFilter, versionFilter, textFilter, textReuseFilter, releaseFilter


@api_view(['GET'])
def apiOverview(request):
    api_urls = {
        # 'List All Books (without filters, will be removed in the future)': '/book-list',
        # 'List All Books (with pagination and filters)': '/book/all',
        # 'Book View': '/book/<book_uri:pk>/ e.g.book/JK00001'
        'List all authors:': 'author/all/',
        'Search authors:': 'author/?search= e.g., `author/all/?search=الجاحظ 255`',
        'Filter authors based on a specific field:': 'author/?author_lat= e.g., `author/?author_lat=Jahiz`',
        'List all texts:': 'text/all/',
        'Get a text by its URI:': 'text/<str:text_uri>/ e.g. `text/0179MalikIbnAnas.Muwatta`',
        'Filter texts based on a specific field:': 'text/?author_lat= e.g., `author/?author_lat=Jahiz`',
        'Search texts:': 'text/all/?search= e.g., `text/all/?search=الجاحظ Hayawan`',
        'List all text versions:': 'version/all/',
        'Search text versions:': 'text/all/?search= e.g., `text/all/?search=الجاحظ Hayawan Shamela`',
        'corpusinsights/':  'gives some overall insights about the corpus',
        'text-reuse-stats/': 'Text resuse stats'
    }

    return Response(api_urls)

# Not in use but useful if we want everything in one go
@api_view(['GET'])
def bookList(request):
    books = versionMeta.objects.all()
    serializer = VersionMetaSerializer(books, many=True)
    return Response(serializer.data)

# Get a text by its text_uri
@api_view(['GET'])
def getText(request, text_uri):

    try:
        text = textMeta.objects.get(text_uri=text_uri)
        serializer = TextSerializer(text, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
        raise Http404

# Get a text version by its version_id
@api_view(['GET'])
def getVersion(request, version_id):

    try:
        version = versionMeta.objects.get(version_id=version_id)
        serializer = VersionMetaSerializer(version, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
        raise Http404



@api_view(['GET'])
def getReleaseVersion(request, release_code, version_id):
    """Get a text version by its version_id and release_id"""

    try:
        release_version = ReleaseMeta.objects.get(release__release_code=release_code, version_meta__version_id=version_id)
        serializer = ReleaseMetaSerializer(release_version, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
        raise Http404
    

@api_view(['GET'])
def getReleaseText(request, release_code, text_uri):
    """Get a text version by its version_id and release_id"""

    try:
        text = textMeta.objects.filter(text_uri=text_uri, version__release__release__release_code=release_code).first()
        serializer = TextSerializer(text, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
        raise Http404


# Get an author record by its author_uri
@api_view(['GET'])
def getAuthor(request, author_uri):

    try:
        author = authorMeta.objects.get(author_uri=author_uri)
        serializer = AuthorMetaSerializer(author, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
        raise Http404


# Get some aggregated stats on the corpus like authors no, book no. etc.
@api_view(['GET'])
def getCorpusInsights(request):
    corpus_insight_stats = CorpusInsights.objects.all()

    serializer = CorpusInsightsSerializer(corpus_insight_stats, many=True)
    # if serializer.is_valid():
    #     serializer.save()
    # else:
    #     save_message = serializer.errors
    #     print(save_message)

    return Response(serializer.data)


# Remove this before going live as we shouldn't allow any POST method
@api_view(['POST'])
def bookCreate(request):
    serializer = VersionMetaSerializer(data=request.data)
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
#             "text", "name_element", "version", "author_meta", "version_id", "text_meta"]      # foreign key fields
excl_flds = [
    # numeric fields:
    "id", "date", "date_AH", "date_CE", "tok_length", "char_length",
    # foreign key fields:
    "text", "name_element", "version", "author_meta", "version_id", "text_meta",
    "related_persons", "related_places", "related_texts", "place_relations",
    "person_a", "person_b", "text_a", "text_b",
    "place_a", "place_b", "relation_type", "parent_type",
    # related fields:
    'authormeta', 'textmeta', 'related_person_a', 'related_person_b',
    "related_text_a", "related_text_b"]


class authorListView(generics.ListAPIView):
    """
    Return a paginated list of author metadata objects
    (each containing metadata on an author, their texts and versions of their texts)
    """
    queryset = authorMeta.objects.all()
    serializer_class = AuthorMetaSerializer
    pagination_class = CustomPagination

    # customize the search:

    search_fields = [field.name for field in authorMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__" + field.name for field in textMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__version__" + field.name for field in versionMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["name_element__" + field.name for field in personName._meta.get_fields()
           if (field.name not in excl_flds)]
    print("AUTHOR SEARCH FIELDS:")
    print(search_fields)
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
    filterset_class = authorFilter

    # old experiments with filters by Sohail:

    # filter_fields ={
    #     #'annotation_status': ['in', 'exact'], # note the 'in'
    #     'text__text_uri': ['exact'],
    #     'text__titles_ar':['exact'] ,
    #     'text__titles_lat':['exact'],
    #     'text__version__version_id':['exact']
    # }

    # print(filter_fields)
    #filter_fields = ['titles_lat', 'book_id', 'titles_ar', 'annotation_status']
    # filter_fields = (filter_fields)
    #ordering_fields = ['titles_lat', 'titles_ar']
    #ordering_fields = (ordering_fields)


class versionListView(generics.ListAPIView):
    queryset = versionMeta.objects.all()
    serializer_class = VersionMetaSerializer
    pagination_class = CustomPagination

    # search_fields = [field.name for field in authorMeta._meta.get_fields() if(field.name not in ["text","author_names", 'date', 'date_AH', 'date_CE', 'id'])]+ \
    #["version__"+ field.name for field in textMeta._meta.get_fields() if(field.name not in ["version","id", 'authorMeta'])]\
    #+ ["text__version__"+ field.name for field in versionMeta._meta.get_fields() if(field.name not in ["id", 'textMeta','tok_length','char_length'])]\
    #+ ["author_names__"+ field.name for field in personName._meta.get_fields() if(field.name not in ["id", 'authorMeta'])]
    print("FIELD", versionMeta._meta.get_fields())
    search_fields = [field.name for field in versionMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text_meta__" + field.name for field in textMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text_meta__author_meta__" + field.name for field in authorMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text_meta__author_meta__name_element__" + field.name for field in personName._meta.get_fields() if (field.name not in excl_flds)] \
        + ["release__" + field.name for field in ReleaseMeta._meta.get_fields() if (field.name not in excl_flds)] \

    print("VERSION SEARCH FIELDS:")
    print(search_fields)

    # Customize filtering:

    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = versionFilter

    ordering_fields = ['text_meta__titles_lat', 'text_meta__titles_ar',
                       "text_meta__author_meta__date", 'tok_length']
    ordering_fields = (ordering_fields)


class textListView(generics.ListAPIView):
    queryset = textMeta.objects.all()
    #filter_fields = ['titles_lat', 'book_id', 'titles_ar', 'annotation_status']
    search_fields = [field.name for field in textMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author_meta__" + field.name for field in authorMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author_meta__name_element__" + field.name for field in personName._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version_meta__" + field.name for field in versionMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version_meta__version_meta__" + field.name for field in ReleaseMeta._meta.get_fields() if (field.name not in excl_flds)]

    # print(search_fields)

    #ordering_fields = ['titles_lat', 'titles_ar']
    serializer_class = TextSerializer
    pagination_class = CustomPagination
    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = textFilter
    #filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    # search_fields = (search_fields)
    # filter_fields = (search_fields)
    #ordering_fields = (ordering_fields)


class relationsListView(generics.ListAPIView):
    queryset = a2bRelation.objects.all()
    # for q in queryset:
    #    print(q.text_a)
    serializer_class = AllRelationSerializer

# Text Reuse Stats


class getAllTextReuseStats(generics.ListAPIView):
    serializer_class = ShallowTextReuseStatsSerializer
    pagination_class = CustomPagination

    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = textReuseFilter

    ordering_fields = ['instances_count', 'book1_word_match', 'book2_word_match']
    ordering_fields = (ordering_fields)

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
        print(release_code, book1)
        if release_code:
            if book1:
                queryset = TextReuseStats.objects\
                    .select_related("release", "book_1")\
                    .filter(release__release_code=release_code, book_1__version_uri__contains=book1)\
                    .all()
            else:
                queryset = TextReuseStats.objects\
                    .select_related("release")\
                    .filter(release__release_code=release_code)\
                    .all()
        else:
            if book1:
                queryset = TextReuseStats.objects\
                    .select_related("book_1")\
                    .filter(book_1__version_uri__contains=book1)\
                    .all()
            else:
                print("book1 nor release defined")
                queryset = TextReuseStats.objects.all()
        return queryset

# Get an author record by its author_uri
@api_view(['GET'])
def getPairTextReuseStats(request, book1, book2, release_code=None):
    print(book1, book2, release_code)

    try:
        if release_code:
            stats = TextReuseStats.objects.get(book_1__version_uri__contains=book1, 
                                                  book_2__version_uri__contains=book2, 
                                                  release__release_code=release_code)
            serializer = TextReuseStatsSerializer(stats, many=False)
        else:
            stats = TextReuseStats.objects.filter(book_1__version_uri__contains=book1, 
                                                  book_2__version_uri__contains=book2)
            serializer = TextReuseStatsSerializer(stats, many=True)
        print(stats)
        
        return Response(serializer.data)  
    except TextReuseStats.DoesNotExist:
        raise Http404


class getReleaseMeta(generics.ListAPIView):

    queryset = ReleaseMeta.objects.all()
    
    search_fields = [field.name for field in ReleaseMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version_meta__" + field.name for field in versionMeta._meta.get_fields() if (field.name not in excl_flds)] 
        # + ["version_meta__text_meta__" + field.name for field in textMeta._meta.get_fields() if (field.name not in excl_flds)] \
        # + ["version_meta__text_meta__author_meta__" + field.name for field in authorMeta._meta.get_fields() if (field.name not in excl_flds)] \
        # + ["version_meta__text_meta__author_meta__name_element__" +
        #     field.name for field in personName._meta.get_fields() if (field.name not in excl_flds)]

         ## had to put the list manualy as above function add these two field which makes the code 'version_uri', 'version_uri__release' 
    search_fields = ['release__release_code', 'url', 'analysis_priority', 'annotation_status', 'version_meta__version_uri',  
                     'version_meta__editor', 'version_meta__edition_place', 'version_meta__publisher', 'version_meta__edition_date', 
                     'version_meta__ed_info', 'version_meta__language', 'version_meta__release__tags', 'notes', 
                     'analysis_priority', 'annotation_status', 'version_meta__text_meta__text_uri', 
                     'version_meta__text_meta__titles_ar', 'version_meta__text_meta__titles_lat', 
                     'version_meta__text_meta__title_ar_prefered', 'version_meta__text_meta__title_lat_prefered', 
                     'version_meta__text_meta__text_type', 'version_meta__text_meta__tags', 'version_meta__text_meta__notes', 
                     'version_meta__text_meta__author_meta__author_uri', 
                     'version_meta__text_meta__author_meta__author_ar', 'version_meta__text_meta__author_meta__author_lat', 
                     'version_meta__text_meta__author_meta__author_ar_prefered', 'version_meta__text_meta__author_meta__author_lat_prefered', 
                     'version_meta__text_meta__author_meta__date_str', 'version_meta__text_meta__author_meta__notes', 
                     'version_meta__text_meta__author_meta__name_element__language', 
                     'version_meta__text_meta__author_meta__name_element__shuhra', 'version_meta__text_meta__author_meta__name_element__nasab', 
                     'version_meta__text_meta__author_meta__name_element__kunya', 'version_meta__text_meta__author_meta__name_element__ism', 
                     'version_meta__text_meta__author_meta__name_element__laqab', 'version_meta__text_meta__author_meta__name_element__nisba']

    
    print("RELEASE SEARCH FIELDS:")
    print(search_fields)

    serializer_class = ReleaseMetaSerializer
    pagination_class = CustomPagination

    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = releaseFilter

    ordering_fields = ['tok_length', 'analysis_priority', 'version_meta__text_meta__author_meta__date', 
                       'version_meta__text_meta__title_lat_prefered', 'version_meta__text_meta__author_meta__author_lat_prefered']

    
class getReleaseDetails(generics.ListAPIView):

    queryset = ReleaseDetails.objects.all()
    serializer_class = ReleaseDetailsSerializer


    
class getSourceCollectionDetails(generics.ListAPIView):

    queryset = SourceCollectionDetails.objects.all()
    serializer_class = SourceCollectionDetailsSerializer




