"""Replace pilcrows ¶ in all fields in which they are in the database

The pilcrows are a remnant of the way line breaks are represented 
in the readYML function of the openiti Python library.
They should have been removed on import into the database, 
but that didn't happen for all fields.

Unfortunately, with sqlite, no regular expressions can be used.
"""

from django.db.models import F, Func, Value, TextField
from django.db.models.functions import Replace
from django.core.management.base import BaseCommand

from api.models import Text, Edition, Author



class Command(BaseCommand):
    def handle(self, **options):
        # # https://stackoverflow.com/questions/12371675/django-update-multiple-objects-with-regex/68402017#68402017
        # # this doesn't work because sqlite doesn't support regex by default
        # pattern = Value(' *¶ *')
        # replacement = Value(' ')
        # flags = Value('g')  # regex flags

        # Edition.objects.update(
        #     ed_info=Func(
        #         F('ed_info'),
        #         pattern, replacement, flags,
        #         function='REGEXP_REPLACE',
        #         output_field=TextField(),
        #     )
        # )

        Edition.objects.update(\
            ed_info=Replace("ed_info", 
                            Value("¶"), Value(" ")))
        Edition.objects.update(\
            ed_info=Replace("ed_info", 
                            Value("  "), Value(" ")))
        Text.objects.update(\
            title_ar_prefered=Replace("title_ar_prefered", 
                                      Value("¶"), Value(" ")))
        Text.objects.update(\
            title_ar_prefered=Replace("title_ar_prefered", 
                                      Value("  "), Value(" ")))

        Text.objects.update(\
            title_lat_prefered=Replace("title_lat_prefered", 
                                      Value("¶"), Value(" ")))
        Text.objects.update(\
            title_lat_prefered=Replace("title_lat_prefered", 
                                      Value("  "), Value(" ")))
        
        Text.objects.update(\
            titles_ar=Replace("titles_ar", 
                              Value("¶"), Value(" ")))
        Text.objects.update(\
            titles_ar=Replace("titles_ar", 
                              Value("  "), Value(" ")))

        Text.objects.update(\
            titles_lat=Replace("titles_lat", 
                               Value("¶"), Value(" ")))
        Text.objects.update(\
            titles_lat=Replace("titles_lat", 
                               Value("  "), Value(" ")))

        Author.objects.update(\
            author_lat=Replace("author_lat", 
                               Value("¶"), Value(" ")))
        Author.objects.update(\
            author_lat=Replace("author_lat", 
                               Value("  "), Value(" ")))
        
        Author.objects.update(\
            author_ar=Replace("author_ar", 
                               Value("¶"), Value(" ")))
        Author.objects.update(\
            author_ar=Replace("author_ar", 
                               Value("  "), Value(" ")))
        
        Author.objects.update(\
            notes=Replace("notes", 
                               Value("¶"), Value(" ")))
        Author.objects.update(\
            notes=Replace("notes", 
                               Value("  "), Value(" ")))       