from django.urls import path
from . import views

urlpatterns = [
    path('', views.apiOverview, name='api-overview'),
    path('corpusinsights/', views.getCorpusInsights, name='corpusinsights'),
    path('author/', views.authorListView.as_view(), name='author-list-all'),
    path('author/all/', views.authorListView.as_view(), name='author-list-all'),
    path('author/<str:author_uri>/', views.getAuthor, name='author'),
    path('text/',views.textListView.as_view(), name='text-list-all'),
    path('text/all/',views.textListView.as_view(), name='text-list-all'),
    path('text/<str:text_uri>/', views.getText, name='text'),
    path('version/',views.versionListView.as_view(), name='version-list-all'),
    path('version/all/',views.versionListView.as_view(), name='version-list-all'),
    path('version/<str:version_id>/', views.getVersion, name='version'),
    path('relations/all/', views.relationsListView.as_view(), name='rel'),
    path('release/all/', views.getReleaseMeta.as_view(), name='release'),
    path('release-details/all/', views.getReleaseDetails.as_view(), name='release-details'),
    path('source-collections/all/', views.getSourceCollectionDetails.as_view(), name='source-collections'),
    #path('book-list/', views.bookList, name='book-list'),
    #path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
    #path('book-create/', views.bookCreate, name='book-create')
    path('<str:release_code>/version/<str:version_id>/', views.getReleaseVersion, name='release-version'),
    path('<str:release_code>/text/<str:text_uri>/', views.getReleaseText, name='release-text'),
    # Text reuse statistics, per release:
    path('<str:release_code>/text-reuse-stats/<str:book1>_<book2>/', views.getPairTextReuseStats, name='text-reuse-pair'),
    path('<str:release_code>/text-reuse-stats/all/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
    path('<str:release_code>/text-reuse-stats/<str:book1>/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
    # Text reuse statistics, across releases:
    path('text-reuse-stats/<str:book1>_<book2>/', views.getPairTextReuseStats, name='text-reuse-pair'),
    path('text-reuse-stats/all/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
    path('text-reuse-stats/<str:book1>/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),

]