"""
This module maps the API endpoint URLs to views that will send the requests
to the database and return a JSON response.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_overview, name='api-overview'),

    # Text reuse statistics:

    path('all-releases/text-reuse-stats/<str:book1>_<str:book2>/', views.get_pair_text_reuse_stats, name='text-reuse-pair'),
    path('all-releases/text-reuse-stats/all/', views.TextReuseStatsListView.as_view(), name='all-text-reuse'),
    path('all-releases/text-reuse-stats/', views.TextReuseStatsListView.as_view(), name='all-text-reuse'),
    path('all-releases/text-reuse-stats/<str:book1>/', views.TextReuseStatsB1ListView.as_view(), name='all-text-reuse'),

    path('<str:release_code>/text-reuse-stats/<str:book1>_<str:book2>/', views.get_pair_text_reuse_stats, name='text-reuse-pair'),
    path('<str:release_code>/text-reuse-stats/all/', views.TextReuseStatsListView.as_view(), name='all-text-reuse'),
    path('<str:release_code>/text-reuse-stats/', views.TextReuseStatsListView.as_view(), name='all-text-reuse'),
    path('<str:release_code>/text-reuse-stats/<str:book1>/', views.TextReuseStatsB1ListView.as_view(), name='all-text-reuse'),

    # release version endpoints:

    path('all-releases/version/all/', views.VersionListView.as_view(), name='all-releases-all-versions'),
    path('all-releases/version/', views.VersionListView.as_view(), name='all-releases-all-versions'),
    path('all-releases/version/<str:version_code>/', views.VersionListView.as_view(), name='all-releases-one-version'), # multiple results possible!
    
    # problem: filtering on release_version - specific metadata (pri/sec, markdown/completed) does not work!
    # path('<str:release_code>/version/all/', views.VersionListView.as_view(), name='all-releases-all-versions'),
    # path('<str:release_code>/version/', views.VersionListView.as_view(), name='all-releases-all-versions'),
    # path('<str:release_code>/version/<str:version_code>/', views.get_version, name='one-release-one-version'),
    path('<str:release_code>/version/all/', views.ReleaseVersionListView.as_view(), name='one-release-all-versions'),
    path('<str:release_code>/version/', views.ReleaseVersionListView.as_view(), name='one-release-all-versions'),
    path('<str:release_code>/version/<str:version_code>/', views.get_release_version, name='one-release-one-version'),

    # text endpoints:  # TO DO: use other view for the texts  get_release_text

    path('all-releases/text/', views.TextListView.as_view(), name='all-releases-all-texts'),
    path('all-releases/text/all/', views.TextListView.as_view(), name='all-releases-all-texts'),
    path('all-releases/text/<str:text_uri>/', views.get_text, name='all-releases-one-text'),

    path('<str:release_code>/text/', views.TextListView.as_view(), name='one-release-all-texts'),
    path('<str:release_code>/text/all/', views.TextListView.as_view(), name='one-release-all-texts'),
    path('<str:release_code>/text/<str:text_uri>/', views.get_text, name='one-release-one-text'),

    # author endpoints:

    path('all-releases/author/', views.AuthorListView.as_view(), name='all-releases-all-authors'),
    path('all-releases/author/all/', views.AuthorListView.as_view(), name='all-releases-all-authors'),
    path('all-releases/author/<str:author_uri>/', views.get_author, name='all-releases-one-author'),

    path('<str:release_code>/author/', views.AuthorListView.as_view(), name='one-release-all-authors'),
    path('<str:release_code>/author/all/', views.AuthorListView.as_view(), name='one-release-all-authors'),
    path('<str:release_code>/author/<str:author_uri>/', views.get_author, name='one-release-one-author'),

    # release info endpoints:

    path('all-releases/release-info/', views.GetReleaseInfoList.as_view(), name='all-release-info'),
    path('<str:release_code>/release-info/', views.get_release_info, name='release-info'),

    # A2BRelations endpoints (independent of releases):

    path('relation/all/', views.RelationsListView.as_view(), name='all-releases-relations'),
    path('relation/', views.RelationsListView.as_view(), name='all-releases-relations'),

    # relation types endpoint:
    path('relation-type/all/', views.RelationTypesListView.as_view(), name='all-releases-relations'),
    path('relation-type/<str:code>/', views.get_relation_type, name='all-releases-relations'),

    # source collections info (independent of releases):

    path('source-collection/all/', views.GetSourceCollectionDetailsList.as_view(), name='all-source-collections'),
    path('source-collection/', views.GetSourceCollectionDetailsList.as_view(), name='all-source-collections'),
    path('source-collection/<str:code>/', views.get_source_collection, name='source-collection'),

    # corpus insights (statistics on the number of books, largest book, etc. for each release):
    
    path('all-releases/corpusinsights/', views.get_corpus_insights, name='corpusinsights'),
    path('<str:release_code>/corpusinsights/', views.get_corpus_insights, name='corpusinsights'),

    # Person names endpoints: 

    path('person-name/all/', views.PersonNameListView.as_view(), name='person-names-all'),

    # GitHub Issues endpoints (temporary): TO DO: version this endpoint + create view for single issue?

    path('github-issue/all/', views.GitHubIssuesListView.as_view(), name='github-issues'),
]









### OLD PATHS, NOT IN USE ANYMORE ###
# urlpatterns = [

#     # version endpoints: (a confusing category - we should use the releaseMeta as starting point!)

#     path('all-releases/version/', views.VersionListView.as_view(), name='all-releases-all-versions'),
#     path('all-releases/version/all/', views.VersionListView.as_view(), name='all-releases-all-versions'),
#     path('all-releases/version/<str:version_code>/', views.get_version, name='all-releases-one-version'),

#     path('<str:release_code>/version/', views.VersionListView.as_view(), name='one-release-all-versions'),
#     path('<str:release_code>/version/all/', views.VersionListView.as_view(), name='one-release-all-versions'),
#     path('<str:release_code>/version/<str:version_code>/', views.get_version, name='one-release-one-version'),

#     path('all-releases/version/all/', views.get_release_version.as_view(), name='all-releases-all-versions'),
#     path('all-releases/version/', views.get_release_version.as_view(), name='all-releases-all-versions'),
#     path('all-releases/version/<str:version_code>/', views.get_release_version.as_view(), name='all-releases-one-version'), # multiple results possible!

#     path('<str:release_code>/version/all/', views.get_release_version.as_view(), name='one-release-all-versions'),
#     path('<str:release_code>/version/', views.get_release_version.as_view(), name='one-release-all-versions'),
#     path('<str:release_code>/version/<str:version_code>/', views.get_release_version, name='one-release-one-version'),

#     path('book-list/', views.book_list, name='book-list'),
#     path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
#     path('book-create/', views.book_create, name='book-create')



#     path('', views.api_overview, name='api-overview'),
#     path('corpusinsights/', views.get_corpus_insights, name='corpusinsights'),
#     path('author/', views.AuthorListView.as_view(), name='author-list-all'),
#     path('author/all/', views.AuthorListView.as_view(), name='author-list-all'),
#     path('author/<str:author_uri>/', views.get_author, name='author'),
#     path('text/',views.TextListView.as_view(), name='text-list-all'),
#     path('text/all/',views.TextListView.as_view(), name='text-list-all'),
#     path('text/<str:text_uri>/', views.get_text, name='text'),
#     path('version/',views.VersionListView.as_view(), name='version-list-all'),
#     path('version/all/',views.VersionListView.as_view(), name='version-list-all'),
#     path('version/<str:version_code>/', views.get_version, name='version'),
#     path('relations/all/', views.RelationsListView.as_view(), name='rel'),
#     path('release/all/', views.get_release_version.as_view(), name='release'),
#     path('release-details/all/', views.get_release_info.as_view(), name='release-details'),
#     path('source-collections/all/', views.GetSourceCollectionDetails.as_view(), name='source-collections'),
#     #path('book-list/', views.book_list, name='book-list'),
#     #path('book-detail/<str:pk>/', views.bookDetail, name='book-detail'),
#     #path('book-create/', views.book_create, name='book-create')
#     path('<str:release_code>/version/<str:version_code>/', views.get_release_version, name='release-version'),
#     path('<str:release_code>/text/<str:text_uri>/', views.get_release_text, name='release-text'),
#     # Text reuse statistics, per release:
#     path('<str:release_code>/text-reuse-stats/<str:book1>_<book2>/', views.get_pair_text_reuse_stats, name='text-reuse-pair'),
#     path('<str:release_code>/text-reuse-stats/all/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),
#     path('<str:release_code>/text-reuse-stats/<str:book1>/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),
#     # Text reuse statistics, across releases:
#     path('text-reuse-stats/<str:book1>_<book2>/', views.get_pair_text_reuse_stats, name='text-reuse-pair'),
#     path('text-reuse-stats/all/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),
#     path('text-reuse-stats/<str:book1>/', views.GetAllTextReuseStats.as_view(), name='all-text-reuse'),
# ]