from typing import Text
from django.contrib import admin

# Register your models here.
from .models import personName, textMeta, authorMeta, versionMeta, AggregatedStats

admin.site.register(textMeta)
admin.site.register(authorMeta)
admin.site.register(personName)
admin.site.register(versionMeta)
admin.site.register(AggregatedStats)
