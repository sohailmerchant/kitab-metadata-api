from django.urls import path
from . import views

urlpatterns = [
    path('', views.apiOverview, name='api-overview'),
    path('book/', views.getText, name='book'),
    path('book/<str:pk>/', views.getText, name='book'),
    path('aggregatedstats/', views.getAggregatedStats, name='aggregatedstats'),
     path('author/all/', views.authorListView.as_view(), name='author-list-all'),
    path('version/all/',views.versionListView.as_view(), name='version-list-all'),
    path('text/all/',views.textListView.as_view(), name='text-list-all'),
    path('text/<str:pk>/', views.getText, name='text'),

      #path('book-list/', views.bookList, name='book-list'),
    #path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
    #path('book-create/', views.bookCreate, name='book-create')

]