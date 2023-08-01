from typing import Text
from django.contrib import admin

# Register your models here.
from .models import PersonName, Text, Author, Version, CorpusInsights, ReleaseVersion, A2BRelation, RelationType, Place, TextReuseStats ,SourceCollectionDetails,ReleaseInfo
admin.site.register(Text)
admin.site.register(Author)
admin.site.register(PersonName)
admin.site.register(Version)
admin.site.register(A2BRelation)
admin.site.register(RelationType)
admin.site.register(Place)
admin.site.register(CorpusInsights)
admin.site.register(TextReuseStats)
admin.site.register(ReleaseVersion)
admin.site.register(ReleaseInfo)
admin.site.register(SourceCollectionDetails)
