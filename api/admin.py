from typing import Text
from django.contrib import admin

# Register your models here.
from .models import authorName, textMeta, authorMeta, versionMeta, AggregatedStats

admin.site.register(textMeta)
admin.site.register(authorMeta)
admin.site.register(authorName)
admin.site.register(versionMeta)
admin.site.register(AggregatedStats)
