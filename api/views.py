from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404

from rest_framework import generics, status
from rest_framework import pagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as django_filters
from rest_framework import filters


from .models import authorMeta, authorName, textMeta, versionMeta, AggregatedStats
from .serializers import TextSerializer,VersionMetaSerializer,AuthorNameSerializer,AuthorMetaSerializer, AggregatedStatsSerializer

@api_view(['GET'])
def apiOverview(request):
    api_urls = {
        #'List All Books (without filters, will be removed in the future)': '/book-list',
        'List All Books (with pagination and filters)': '/book/all',
        'Book View': '/book/<book_uri:pk>/ e.g.book/JK00001'
    }

    return Response(api_urls)

## Not in use but useful if we want everything in one go
@api_view(['GET'])
def bookList(request):
    books = versionMeta.objects.all()
    serializer = VersionMetaSerializer(books, many=True)
    return Response(serializer.data)

## Get a text by text_uri
@api_view(['GET'])
def getText(request, pk):
    
    try:
        text = textMeta.objects.get(text_uri = pk )
        serializer = TextSerializer(text, many=False)
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

class authorListView(generics.ListAPIView):
    queryset = authorMeta.objects.all()

   ## By doing this we can do multiple value filter with '__in' /book/all/?annotation_status__in=inProgress,mARkdown

    filter_fields ={
        #'annotation_status': ['in', 'exact'], # note the 'in'
        'text__text_uri': ['exact'],
        'text__title_ar':['exact'] ,
        'text__title_lat':['exact'],
        'text__version__version_id':['exact']
    }

    search_fields = [field.name for field in authorMeta._meta.get_fields() if(field.name not in ["text","author_names", 'date', 'authorDateAH', 'authorDateCE', 'id'])]+ \
    ["text__"+ field.name for field in textMeta._meta.get_fields() if(field.name not in ["version","id", 'authorMeta'])]\
    + ["text__version__"+ field.name for field in versionMeta._meta.get_fields() if(field.name not in ["id", 'textMeta','tok_length','char_length'])]\
    + ["author_names__"+ field.name for field in authorName._meta.get_fields() if(field.name not in ["id", 'authorMeta'])]
    
    # print(search_fields)

    #filter_fields = ['title_lat', 'book_id', 'title_ar', 'annotation_status']
    #ordering_fields = ['title_lat', 'title_ar']
    serializer_class = AuthorMetaSerializer 
    pagination_class = CustomPagination
    filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    search_fields = (search_fields)
    filter_fields = (filter_fields)
    #ordering_fields = (ordering_fields)


class versionListView(generics.ListAPIView):
    queryset = versionMeta.objects.all()

    search_fields = [field.name for field in authorMeta._meta.get_fields() if(field.name not in ["text","author_names", 'date', 'authorDateAH', 'authorDateCE', 'id'])]+ \
    ["version__"+ field.name for field in textMeta._meta.get_fields() if(field.name not in ["version","id", 'authorMeta'])]\
    + ["text__version__"+ field.name for field in versionMeta._meta.get_fields() if(field.name not in ["id", 'textMeta','tok_length','char_length'])]\
    + ["author_names__"+ field.name for field in authorName._meta.get_fields() if(field.name not in ["id", 'authorMeta'])]
    
    print(search_fields)

    filter_fields = ['version_id', 'version_uri', "text_uri__text_uri", "text_uri__title_ar", "text_uri__title_lat", "status"]
    ordering_fields = ['title_lat', 'title_ar', "text_uri__author_uri__date"]
    serializer_class = VersionMetaSerializer 
    pagination_class = CustomPagination
    filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    #search_fields = (search_fields)
    filter_fields = (filter_fields)
    ordering_fields = (ordering_fields)

class textListView(generics.ListAPIView):
    queryset = textMeta.objects.all()
    #filter_fields = ['title_lat', 'book_id', 'title_ar', 'annotation_status']
    #ordering_fields = ['title_lat', 'title_ar']
    serializer_class = TextSerializer 
    pagination_class = CustomPagination
    filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    # search_fields = (search_fields)
    # filter_fields = (search_fields)
    #ordering_fields = (ordering_fields)