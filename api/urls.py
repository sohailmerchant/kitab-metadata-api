from django.urls import path
from . import views

urlpatterns = [
    path('', views.apiOverview, name='api-overview'),
    path('aggregatedstats/', views.getAggregatedStats, name='aggregatedstats'),
    #path('author/', views.authorListView.as_view(), name='author-list-all'),
    path('author/', views.authorListView.as_view(), name='author-list-all'),
    path('author/all/', views.author_view, name='author-list'),
    path('author/<str:author_uri>/', views.getAuthor, name='author'),
    path('text/',views.textListView.as_view(), name='text-list-all'),
    path('text/all/',views.textListView.as_view(), name='text-list-all'),
    path('text/<str:text_uri>/', views.getText, name='text'),
    path('version/',views.versionListView.as_view(), name='version-list-all'),
    path('version/all/',views.versionListView.as_view(), name='version-list-all'),
    path('version/<str:version_id>/', views.getVersion, name='version'),
    path('relations/all/', views.relationsListView.as_view(), name='rel')

    #path('book-list/', views.bookList, name='book-list'),
    #path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
    #path('book-create/', views.bookCreate, name='book-create')

]