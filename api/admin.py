from typing import Text
from django.contrib import admin

# Register your models here.
from .models import personName, textMeta, authorMeta, versionMeta, CorpusInsights, ReleaseMeta, a2bRelation, relationType, placeMeta, TextReuseStats ,SourceCollectionDetails,ReleaseDetails
admin.site.register(textMeta)
admin.site.register(authorMeta)
admin.site.register(personName)
admin.site.register(versionMeta)
admin.site.register(a2bRelation)
admin.site.register(relationType)
admin.site.register(placeMeta)
admin.site.register(CorpusInsights)
admin.site.register(TextReuseStats)
admin.site.register(ReleaseMeta)
admin.site.register(ReleaseDetails)
admin.site.register(SourceCollectionDetails)
