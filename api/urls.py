from django.urls import path
from . import views

urlpatterns = [
    path('', views.apiOverview, name='api-overview'),

    # release version endpoints:

    path('all-releases/version/all/', views.getReleaseMeta.as_view(), name='all-releases-all-versions'),
    path('all-releases/version/', views.getReleaseMeta.as_view(), name='all-releases-all-versions'),
    #path('all-releases/version/<str:version_id>/', views.getReleaseMeta.as_view(), name='all-releases-one-version'), # multiple results possible!
    path('all-releases/version/<str:version_id>/', views.getVersion, name='all-releases-one-version'),
    
    path('<str:release_code>/version/all/', views.getReleaseMeta.as_view(), name='one-release-all-versions'),
    path('<str:release_code>/version/', views.getReleaseMeta.as_view(), name='one-release-all-versions'),
    path('<str:release_code>/version/<str:version_id>/', views.getReleaseVersion, name='one-release-one-version'),

    # text endpoints:  # TO DO: use other view for the texts

    path('all-releases/text/', views.textListView.as_view(), name='all-releases-all-texts'),
    path('all-releases/text/all/', views.textListView.as_view(), name='all-releases-all-texts'),
    path('all-releases/text/<str:text_uri>/', views.getText, name='all-releases-one-text'),

    path('<str:release_code>/text/', views.textListView.as_view(), name='one-release-all-texts'),
    path('<str:release_code>/text/all/', views.textListView.as_view(), name='one-release-all-texts'),
    path('<str:release_code>/text/<str:text_uri>/', views.getText, name='one-release-one-text'),

    # author endpoints:

    path('all-releases/author/', views.authorListView.as_view(), name='all-releases-all-authors'),
    path('all-releases/author/all/', views.authorListView.as_view(), name='all-releases-all-authors'),
    path('all-releases/author/<str:author_uri>/', views.getAuthor, name='all-releases-one-author'),

    path('<str:release_code>/author/', views.authorListView.as_view(), name='one-release-all-authors'),
    path('<str:release_code>/author/all/', views.authorListView.as_view(), name='one-release-all-authors'),
    path('<str:release_code>/author/<str:author_uri>/', views.getAuthor, name='one-release-one-author'),

    # release info endpoints:

    path('all-releases/release-details/', views.getReleaseDetailsList.as_view(), name='release-details-all'),
    path('<str:release_code>/release-details/', views.getReleaseInfo, name='release-details'),

    # a2bRelations endpoints (independent of releases):

    path('all-releases/relation/all/', views.relationsListView.as_view(), name='all-releases-relations'),
    path('all-releases/relation/', views.relationsListView.as_view(), name='all-releases-relations'),

    # source collections info (independent of releases):

    path('source-collections/all/', views.getSourceCollectionDetailsList.as_view(), name='source-collections'),
    path('source-collections/', views.getSourceCollectionDetailsList.as_view(), name='source-collections'),
    path('source-collections/<str:code>', views.getSourceCollectionDetailsList.as_view(), name='source-collections'),

    # corpus insights (statistics on the number of books, largest book, etc. for each release):
    
    path('all-releases/corpusinsights/', views.getCorpusInsights, name='corpusinsights'),
    path('<str:release_code>/corpusinsights/', views.getCorpusInsights, name='corpusinsights'),

    # Text reuse statistics:

    path('all-releases/text-reuse-stats/<str:book1>_<str:book2>/', views.getPairTextReuseStats, name='text-reuse-pair'),
    path('all-releases/text-reuse-stats/all/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
    path('all-releases/text-reuse-stats/<str:book1>/', views.getAllTextReuseStatsB1.as_view(), name='all-text-reuse'),

    path('<str:release_code>/text-reuse-stats/<str:book1>_<str:book2>/', views.getPairTextReuseStats, name='text-reuse-pair'),
    path('<str:release_code>/text-reuse-stats/all/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
    path('<str:release_code>/text-reuse-stats/<str:book1>/', views.getAllTextReuseStatsB1.as_view(), name='all-text-reuse'),

    # # version endpoints: (a confusing category - we should use the releaseMeta as starting point!)

    # path('all-releases/version/', views.versionListView.as_view(), name='all-releases-all-versions'),
    # path('all-releases/version/all/', views.versionListView.as_view(), name='all-releases-all-versions'),
    # path('all-releases/version/<str:version_id>/', views.getVersion, name='all-releases-one-version'),

    # path('<str:release_code>/version/', views.versionListView.as_view(), name='one-release-all-versions'),
    # path('<str:release_code>/version/all/', views.versionListView.as_view(), name='one-release-all-versions'),
    # path('<str:release_code>/version/<str:version_id>/', views.getVersion, name='one-release-one-version'),


    #path('book-list/', views.bookList, name='book-list'),
    #path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
    #path('book-create/', views.bookCreate, name='book-create')


]


# urlpatterns = [
#     path('', views.apiOverview, name='api-overview'),
#     path('corpusinsights/', views.getCorpusInsights, name='corpusinsights'),
#     path('author/', views.authorListView.as_view(), name='author-list-all'),
#     path('author/all/', views.authorListView.as_view(), name='author-list-all'),
#     path('author/<str:author_uri>/', views.getAuthor, name='author'),
#     path('text/',views.textListView.as_view(), name='text-list-all'),
#     path('text/all/',views.textListView.as_view(), name='text-list-all'),
#     path('text/<str:text_uri>/', views.getText, name='text'),
#     path('version/',views.versionListView.as_view(), name='version-list-all'),
#     path('version/all/',views.versionListView.as_view(), name='version-list-all'),
#     path('version/<str:version_id>/', views.getVersion, name='version'),
#     path('relations/all/', views.relationsListView.as_view(), name='rel'),
#     path('release/all/', views.getReleaseMeta.as_view(), name='release'),
#     path('release-details/all/', views.getReleaseDetails.as_view(), name='release-details'),
#     path('source-collections/all/', views.getSourceCollectionDetails.as_view(), name='source-collections'),
#     #path('book-list/', views.bookList, name='book-list'),
#     #path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
#     #path('book-create/', views.bookCreate, name='book-create')
#     path('<str:release_code>/version/<str:version_id>/', views.getReleaseVersion, name='release-version'),
#     path('<str:release_code>/text/<str:text_uri>/', views.getReleaseText, name='release-text'),
#     # Text reuse statistics, per release:
#     path('<str:release_code>/text-reuse-stats/<str:book1>_<book2>/', views.getPairTextReuseStats, name='text-reuse-pair'),
#     path('<str:release_code>/text-reuse-stats/all/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
#     path('<str:release_code>/text-reuse-stats/<str:book1>/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
#     # Text reuse statistics, across releases:
#     path('text-reuse-stats/<str:book1>_<book2>/', views.getPairTextReuseStats, name='text-reuse-pair'),
#     path('text-reuse-stats/all/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
#     path('text-reuse-stats/<str:book1>/', views.getAllTextReuseStats.as_view(), name='all-text-reuse'),
# ]