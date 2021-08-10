from django.urls import path
from . import views

urlpatterns = [
    path('', views.apiOverview, name='api-overview'),
    path('book/', views.getBook, name='book'),
    path('book/all/', views.bookListView.as_view(), name='book-list-all'),
    path('book/<str:pk>/', views.getBook, name='book'),

      #path('book-list/', views.bookList, name='book-list'),
    #path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
    #path('book-create/', views.bookCreate, name='book-create')

]