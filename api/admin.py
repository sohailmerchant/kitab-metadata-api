from typing import Text
from django.contrib import admin

# Register your models here.
from .models import personName, textMeta, authorMeta, versionMeta, AggregatedStats, a2bRelation, relationType, placeMeta

admin.site.register(textMeta)
admin.site.register(authorMeta)
admin.site.register(personName)
admin.site.register(versionMeta)
admin.site.register(a2bRelation)
admin.site.register(relationType)
admin.site.register(placeMeta)
admin.site.register(AggregatedStats)
