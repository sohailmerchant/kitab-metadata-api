from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404

from rest_framework import generics, status
from rest_framework import pagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as django_filters
from rest_framework import filters


from .models import Book, AggregatedStats
from .serializers import BookSerializer, AggregatedStatsSerializer

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
    books = Book.objects.all()
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)

## Get a book by book_uri
@api_view(['GET'])
def getBook(request, pk):
    try:
        book = Book.objects.get(book_id = pk )
        serializer = BookSerializer(book, many=False)
        return Response(serializer.data)
    except Book.DoesNotExist:
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
    serializer = BookSerializer(data=request.data)
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
        max_page_size = 100
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

class bookListView(generics.ListAPIView):
    
    queryset = Book.objects.all()
    search_fields = ['title_lat', 'book_id', 'title_ar', 'annotation_status']

    ## By doing this we can do multiple value filter with '__in' /book/all/?annotation_status__in=inProgress,mARkdown

    filter_fields ={
        'annotation_status': ['in', 'exact'], # note the 'in'
        'book_id': ['exact'],
        'title_ar':['exact'] ,
        'title_lat':['exact']
    }
    #filter_fields = ['title_lat', 'book_id', 'title_ar', 'annotation_status']
    ordering_fields = ['title_lat', 'book_id', 'title_ar']
    serializer_class = BookSerializer
    pagination_class = CustomPagination
    filter_backends = (django_filters.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)    
    search_fields = (search_fields)
    filter_fields = (filter_fields)
    ordering_fields = (ordering_fields)

        