from typing import Text
from django.contrib import admin

# Register your models here.
from .models import ObjectName, ObjectNameLink, Calendar, DateType, \
    Date, DateLink, IdentifierProvider, \
    ExternalID, ExternalIDLink, TextType, TextTypeLink, \
    AuthorshipRole, AuthorshipRoleLink, PlaceRelationType, PlaceLink, \
    Author, Text, Version, Edition, \
    ManuscriptHolding, Manuscript, Country, Place, \
    RelationType, A2BRelation, TextReuseStats, CorpusInsights, \
    ReleaseVersion, VersionwiseReuseStats, ReleaseInfo, \
    SourceCollectionDetails, GitHubIssue, GitHubIssueLabel

admin.site.register(ObjectName)
admin.site.register(ObjectNameLink)
admin.site.register(Calendar)
admin.site.register(DateType)
admin.site.register(Date)
admin.site.register(DateLink)
admin.site.register(IdentifierProvider)
admin.site.register(ExternalID)
admin.site.register(ExternalIDLink)
admin.site.register(TextType)
admin.site.register(TextTypeLink)
admin.site.register(AuthorshipRole)
admin.site.register(AuthorshipRoleLink)
admin.site.register(PlaceRelationType)
admin.site.register(PlaceLink)
admin.site.register(Author)
admin.site.register(Text)
admin.site.register(Version)
admin.site.register(Edition)
admin.site.register(ManuscriptHolding)
admin.site.register(Manuscript)
admin.site.register(Country)
admin.site.register(Place)
admin.site.register(RelationType)
admin.site.register(A2BRelation)
admin.site.register(TextReuseStats)
admin.site.register(CorpusInsights)
admin.site.register(ReleaseVersion)
admin.site.register(VersionwiseReuseStats)
admin.site.register(ReleaseInfo)
admin.site.register(SourceCollectionDetails)
admin.site.register(GitHubIssue)
admin.site.register(GitHubIssueLabel)

