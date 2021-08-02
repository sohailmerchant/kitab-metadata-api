from django.urls import path
from . import views

urlpatterns = [
    path('', views.apiOverview, name='api-overview'),
    path('book-list/', views.bookList, name='book-list'),
    path('book-list-all/', views.bookListView.as_view(), name='book-list-all'),
    path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
    path('book-create/', views.bookCreate, name='book-create')

]