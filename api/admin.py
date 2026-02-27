from typing import Text
from django.contrib import admin

# Register your models here.
from .models import Author, RelationType, A2BRelation, ReleaseInfo,\
    Date, DateLink, Calendar, DateType, ObjectName, ObjectNameLink,\
    TextType, TextTypeLink, Text, Edition, \
    Version, SourceCollectionDetails, ReleaseVersion, Contributor #, AuthorshipRole, AuthorshipRoleLink , IdentifierProvider, \
    #ExternalID, ExternalIDLink, \
    #AuthorshipRole, AuthorshipRoleLink, PlaceRelationType, PlaceLink, \
    #ManuscriptHolding, Manuscript, Country, Place, \
    #TextReuseStats, CorpusInsights, \
    #VersionwiseReuseStats, \
    #GitHubIssue, GitHubIssueLabel

admin.site.register(ObjectName)
admin.site.register(ObjectNameLink)
admin.site.register(Calendar)
admin.site.register(DateType)
admin.site.register(Date)
admin.site.register(DateLink)
##admin.site.register(IdentifierProvider)
##admin.site.register(ExternalID)
##admin.site.register(ExternalIDLink)
admin.site.register(TextType)
admin.site.register(TextTypeLink)
#admin.site.register(AuthorshipRole)
#admin.site.register(AuthorshipRoleLink)
##admin.site.register(PlaceRelationType)
##admin.site.register(PlaceLink)
admin.site.register(Author)
admin.site.register(Text)
admin.site.register(Version)
admin.site.register(Edition)
##admin.site.register(ManuscriptHolding)
##admin.site.register(Manuscript)
##admin.site.register(Country)
##admin.site.register(Place)
admin.site.register(RelationType)
admin.site.register(A2BRelation)
##admin.site.register(TextReuseStats)
##admin.site.register(CorpusInsights)
admin.site.register(ReleaseVersion)
##admin.site.register(VersionwiseReuseStats)
admin.site.register(ReleaseInfo)
admin.site.register(SourceCollectionDetails)
##admin.site.register(GitHubIssue)
##admin.site.register(GitHubIssueLabel)
admin.site.register(Contributor)

