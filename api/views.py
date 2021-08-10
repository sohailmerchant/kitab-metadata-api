from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters

from .models import Book
from .serializers import BookSerializer

@api_view(['GET'])
def apiOverview(request):
    api_urls = {
        #'List All Books (without filters, will be removed in the future)': '/book-list',
        'List All Books (with pagination and filters)': '/book/all',
        'Book View': '/book/<book_uri:pk>/ e.g.book/JK00001'
    }

    return Response(api_urls)


@api_view(['GET'])
def bookList(request):
    books = Book.objects.all()
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getBook(request, pk):
    try:
        book = Book.objects.get(book_id = pk )
        serializer = BookSerializer(book, many=False)
        return Response(serializer.data)
    except Book.DoesNotExist:
            raise Http404
      
@api_view(['POST'])
def bookCreate(request):
    serializer = BookSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class bookListView(generics.ListAPIView):
    
    queryset = Book.objects.all()
    fields = ['title_lat', 'book_id', 'title_ar']
    serializer_class = BookSerializer
    pagination_class = PageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)

# class bookListView(generics.ListAPIView):
    
#     queryset = Book.objects.all()
#     serializer_class = BookSerializer
#     pagination_class = PageNumberPagination
#     filter_backends = (filters.DjangoFilterBackend,)
#     filterset_fields = ['title_lat', 'book_id', 'title_ar']
    


        