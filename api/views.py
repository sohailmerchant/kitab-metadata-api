from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404

from rest_framework import generics, status
from rest_framework import pagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as django_filters
from rest_framework import filters


from .models import authorMeta, personName, textMeta, versionMeta, AggregatedStats,a2bRelation
from .serializers import TextSerializer,VersionMetaSerializer,personNameSerializer,AuthorMetaSerializer, AggregatedStatsSerializer,AllRelationSerializer
from .filters import authorFilter, versionFilter, textFilter

@api_view(['GET'])
def apiOverview(request):
    api_urls = {
        #'List All Books (without filters, will be removed in the future)': '/book-list',
        #'List All Books (with pagination and filters)': '/book/all',
        #'Book View': '/book/<book_uri:pk>/ e.g.book/JK00001'
        'List all authors:': 'author/all/',
        'Search authors:': 'author/?search= e.g., `author/all/?search=الجاحظ 255`',
        'Filter authors based on a specific field:': 'author/?author_lat= e.g., `author/?author_lat=Jahiz`',
        'List all texts:': 'text/all/',
        'Get a text by its URI:': 'text/<str:text_uri>/ e.g. `text/0179MalikIbnAnas.Muwatta`',
        'Filter texts based on a specific field:': 'text/?author_lat= e.g., `author/?author_lat=Jahiz`',
        'Search texts:': 'text/all/?search= e.g., `text/all/?search=الجاحظ Hayawan`',
        'List all text versions:': 'version/all/',
        'Search text versions:': 'text/all/?search= e.g., `text/all/?search=الجاحظ Hayawan Shamela`',
    }

    return Response(api_urls)

## Not in use but useful if we want everything in one go
@api_view(['GET'])
def bookList(request):
    books = versionMeta.objects.all()
    serializer = VersionMetaSerializer(books, many=True)
    return Response(serializer.data)

## Get a text by its text_uri
@api_view(['GET'])
def getText(request, text_uri):
    
    try:
        text = textMeta.objects.get(text_uri = text_uri)
        serializer = TextSerializer(text, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
            raise Http404

## Get a text version by its version_id
@api_view(['GET'])
def getVersion(request, version_id):
    
    try:
        version = versionMeta.objects.get(version_id = version_id )
        serializer = VersionMetaSerializer(version, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
            raise Http404

## Get an author record by its author_uri
@api_view(['GET'])
def getAuthor(request, author_uri):
    
    try:
        author = authorMeta.objects.get(author_uri = author_uri )
        serializer = AuthorMetaSerializer(author, many=False)
        return Response(serializer.data)
    except textMeta.DoesNotExist:
            raise Http404


## Get some aggregated stats on the corpus like authors no, book no. etc.
@api_view(['GET'])
def getAggregatedStats(request):
    aggregatedstats = AggregatedStats.objects.all()
    
    serializer = AggregatedStatsSerializer(aggregatedstats, many=True)
    # if serializer.is_valid():
    #     serializer.save()
    # else:
    #     save_message = serializer.errors
    #     print(save_message)
        
    return Response(serializer.data)

## Remove this before going live as we shouldn't allow any POST method      
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
#excl_flds = ["id", "date", "authorDateAH", "authorDateCE", "tok_length", "char_length",  # numeric fields
#             "text", "personName", "version", "author_id", "version_id", "text_id"]      # foreign key fields
excl_flds = [
    # numeric fields:
    "id", "date", "authorDateAH", "authorDateCE", "tok_length", "char_length",
    # foreign key fields:
    "text", "personName", "version", "author_id", "version_id", "text_id", 
    "related_persons", "related_places", "related_texts", "place_relations", 
    "person_a_id", "person_b_id", "text_a_id", "text_b_id", 
    "place_a_id", "place_b_id", "relation_type", "parent_type",
    # related fields:
    'authormeta', 'textmeta', 'related_person_a', 'related_person_b',
    "related_text_a", "related_text_b"]

class authorListView(generics.ListAPIView):
    """
    Return a paginated list of author metadata objects
    (each containing metadata on an author, his texts and versions of his texts)
    """
    queryset = authorMeta.objects.all()
    serializer_class = AuthorMetaSerializer 
    pagination_class = CustomPagination

    # customize the search: 
    

    search_fields = [field.name for field in authorMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__"+ field.name for field in textMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text__version__"+ field.name for field in versionMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["personName__"+ field.name for field in personName._meta.get_fields() if (field.name not in excl_flds)]
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
    
    filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    filterset_class = authorFilter

    # old experiments with filters by Sohail:

    ## By doing this we can do multiple value filter with '__in' /book/all/?annotation_status__in=inProgress,mARkdown:

    # filter_fields ={
    #     #'annotation_status': ['in', 'exact'], # note the 'in'
    #     'text__text_uri': ['exact'],
    #     'text__title_ar':['exact'] ,
    #     'text__title_lat':['exact'],
    #     'text__version__version_id':['exact']
    # }
    
    # print(filter_fields)
    #filter_fields = ['title_lat', 'book_id', 'title_ar', 'annotation_status']
    # filter_fields = (filter_fields)
    #ordering_fields = ['title_lat', 'title_ar']
    #ordering_fields = (ordering_fields)



class versionListView(generics.ListAPIView):
    queryset = versionMeta.objects.all()
    serializer_class = VersionMetaSerializer 
    pagination_class = CustomPagination

    #search_fields = [field.name for field in authorMeta._meta.get_fields() if(field.name not in ["text","author_names", 'date', 'authorDateAH', 'authorDateCE', 'id'])]+ \
    #["version__"+ field.name for field in textMeta._meta.get_fields() if(field.name not in ["version","id", 'authorMeta'])]\
    #+ ["text__version__"+ field.name for field in versionMeta._meta.get_fields() if(field.name not in ["id", 'textMeta','tok_length','char_length'])]\
    #+ ["author_names__"+ field.name for field in personName._meta.get_fields() if(field.name not in ["id", 'authorMeta'])]
    search_fields = [field.name for field in versionMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text_id__"+ field.name for field in textMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text_id__author_id__"+ field.name for field in authorMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["text_id__author_id__personName__"+ field.name for field in personName._meta.get_fields() if (field.name not in excl_flds)]
    print("VERSION SEARCH FIELDS:")
    print(search_fields)


    # Customize filtering:
    
    filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    filterset_class = versionFilter


    ordering_fields = ['title_lat', 'title_ar', "text_id__author_id__date"]
    ordering_fields = (ordering_fields)

class textListView(generics.ListAPIView):
    queryset = textMeta.objects.all()
    #filter_fields = ['title_lat', 'book_id', 'title_ar', 'annotation_status']
    search_fields = [field.name for field in textMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author_id__"+ field.name for field in authorMeta._meta.get_fields() if (field.name not in excl_flds)] \
        + ["author_id__personName__"+ field.name for field in personName._meta.get_fields() if (field.name not in excl_flds)] \
        + ["version__"+ field.name for field in versionMeta._meta.get_fields() if (field.name not in excl_flds)]
        
    #print(search_fields)


    #ordering_fields = ['title_lat', 'title_ar']
    serializer_class = TextSerializer 
    pagination_class = CustomPagination
    filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    filterset_class = textFilter
    #filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    # search_fields = (search_fields)
    # filter_fields = (search_fields)
    #ordering_fields = (ordering_fields)

class relationsListView(generics.ListAPIView):
    queryset = a2bRelation.objects.all()
    #for q in queryset:
    #    print(q.text_a_id)
    serializer_class = AllRelationSerializer 