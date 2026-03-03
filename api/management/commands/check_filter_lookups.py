"""
Use this script to test whether lookup paths in the filters are correct.

create a `qs` object that contains all objects in your start model;
then create a "LOOKUPS" list that contains all lookup paths used in your filter;
then test the lookup paths using the test_lookups method.
"""

from django.core.management.base import BaseCommand
from django.core.exceptions import FieldError
from api.models import Version, ReleaseVersion, Author, Text

class Command(BaseCommand):

    def test_lookups(self, LOOKUPS, qs):
        for lookup in LOOKUPS:
            try:
                qs.filter(**{f"{lookup}__isnull": True}).query
                self.stdout.write(self.style.SUCCESS(f"OK   {lookup}"))
            except FieldError as e:
                self.stdout.write(self.style.ERROR(f"FAIL {lookup} -> {e}"))


    def handle(self, *args, **options):
        self.stdout.write("Checking lookups...\n")

        # 1. VersionSearchFilter
        qs = Version.objects.all()

        print("VersionSearchFilter, related_search_fields:")
        
        LOOKUPS = [
            "text__related_texts__text_uri", 
            "text__related_texts__titles__name", 
            # this covers the old title search fields:
            # - "text__related_texts__titles_ar", 
            # - "text__related_texts__titles_lat", 
            "text__related_texts__authors__names__name",
            # this covers the old title search fields:
            # - "text__related_texts__author__author_ar", 
            # - "text__related_texts__author__author_lat",
            "text__related_persons__author_uri", 
            "text__related_persons__names__name",
            # this covers the old title search fields:
            # - "text__related_persons__author_ar", 
            # - "text__related_persons__author_lat",
            "text__text_related__text_uri", 
            "text__text_related__titles__name", 
            # this covers the old title search fields:
            # - "text__text_related__titles_ar", 
            # - "text__text_related__titles_lat",
            "text__text_related__authors__names__name",
            # this covers the old title search fields:
            # - "text__text_related__author__author_ar", 
            # - "text__text_related__author__author_lat", 
            "text__authors__related_persons__author_uri", # "text__author__related_persons__author_uri", 
            "text__authors__related_persons__names__name",
            # this covers the old title search fields:
            # - "text__author__related_persons__author_ar", 
            # - "text__author__related_persons__author_lat",
            # THROUGH FIELDS:
            "text__related_text_a__relation_type__code",
            "text__related_text_b__relation_type__code",
            "text__related_text_a__relation_type__subtype_code",
            "text__related_text_b__relation_type__subtype_code",
            "text__related_text_a__relation_type__name",
            "text__related_text_b__relation_type__name",
            "text__related_text_a__relation_type__name_inverted",
            "text__related_text_b__relation_type__name_inverted",
            "text__related_text_a__relation_type__descr",
            "text__related_text_b__relation_type__descr",
        ]
        self.test_lookups(LOOKUPS, qs)
        print("-------------")
        print("VersionSearchFilter, extended_search_fields:")
        
        LOOKUPS = [
            "release_version__notes", 
            "release_version__tags", 
            "edition__ed_info",   # includes all edition fields in a single string
            "source_coll__name",  
            "source_coll__description", 
            "text__text_types__slug",# "text__text_type", 
            "text__text_types__label",# "text__text_type",
            "text__tags", 
            "text__notes"
        ]
        self.test_lookups(LOOKUPS, qs)

        # 2. ReleaseVersionSearchFilter
        qs = ReleaseVersion.objects.all()

        print("ReleaseVersionSearchFilter, related_search_fields:")

        LOOKUPS = [
            "version__text__related_texts__text_uri", 
            "version__text__related_texts__titles__name", 
                # this covers the old title search fields:
                # - "version__text__related_texts__titles_ar", 
                # - "version__text__related_texts__titles_lat", 
            "version__text__text_related__text_uri", 
            "version__text__text_related__titles__name", 
                # this covers the old title search fields:
                # - "version__text__text_related__titles_ar", 
                # - "version__text__text_related__titles_lat",
            "version__text__related_texts__authors__names__name",
                # this covers the old title search fields:
                # - "version__text__related_texts__author__author_ar", 
                # - "version__text__related_texts__author__author_lat", 
            "version__text__text_related__authors__names__name",
                # this covers the old title search fields:
                # - "version__text__text_related__author__author_ar", 
                # - "version__text__text_related__author__author_lat",
           
            # ALSO SEARCH URI AND NAMES OF PERSONS RELATED TO THE TEXT:
           
            "version__text__related_persons__author_uri",
            "version__text__related_persons__names__name",
                # this covers the old title search fields:
                # - "version__text__related_persons__author_ar", 
                # - "version__text__related_persons__author_lat",

            # ALSO SEARCH URI AND NAMES OF PERSONS RELATED TO THE AUTHOR:
 
            "version__text__authors__related_persons__author_uri", # "version__text__author__related_persons__author_uri", 
            "version__text__authors__related_persons__names__name",
                # this covers the old title search fields:
                # - "version__text__author__related_persons__author_ar", 
                # - "version__text__author__related_persons__author_lat",
            # ALSO SEARCH THROUGH FIELDS:
            
            "version__text__related_text_a__relation_type__code",
            "version__text__related_text_b__relation_type__code",
            "version__text__related_text_a__relation_type__subtype_code",
            "version__text__related_text_b__relation_type__subtype_code",
            "version__text__related_text_a__relation_type__name",
            "version__text__related_text_b__relation_type__name",
            "version__text__related_text_a__relation_type__name_inverted",
            "version__text__related_text_b__relation_type__name_inverted",
            "version__text__related_text_a__relation_type__descr",
            "version__text__related_text_b__relation_type__descr",
            ##"version__text__authors__related_places__relation_type__code"
        ]
        self.test_lookups(LOOKUPS, qs)

        print("ReleaseVersionSearchFilter, extended_search_fields:")

        LOOKUPS = [
            "notes", 
            "tags", 
            "version__edition__ed_info",   # includes all edition fields in a single string
            "version__source_coll__name",  
            "version__source_coll__description", 
            "version__text__text_types__slug", # "version__text__text_type", 
            "version__text__text_types__label", # "version__text__text_type", 
            "version__text__tags", 
            "version__text__notes"

        ]
        self.test_lookups(LOOKUPS, qs)

        print("3. VersionFilter")

        qs = Version.objects.all()

        LOOKUPS =  [
            "text__authors__author_uri", # "text__author__author_uri",
            "text__authors__names__name", #"text__authors__author_ar",
            "text__authors__names__name", #"text__author__author_lat",
            "text__author__name_element__shuhra", #"text__author__name_element__shuhra", 
            "text__authors__names__name_type",
            "text__authors__names__name",
            "text__author__name_element__ism",
            "text__author__name_element__nasab",
            "text__author__name_element__kunya",
            "text__author__name_element__laqab",
            "text__author__name_element__nisba", 
            "text__authors__dates__year",
            "text__author__date_AH",
            "text__titles__name",
            "text__titles_ar",
            "text__titles_lat",
            "release_version__tok_length", 
            "release_version__char_length",
            "edition__editor", 
            "edition__publisher", 
            "edition__edition_place",
            "edition__edition_date",
            "edition__ed_info",
            "text__titles__language",
            "release_version__char_length",
            "edition__dates__date_str",
            "release_version__analysis_priority",
            "release_version__annotation_status",
            "release_version__tags",
            "text__tags"
        ]    

        self.test_lookups(LOOKUPS, qs)

        print("4. AuthorFilter")

        qs = Author.objects.all()

        LOOKUPS =  [
            "texts__titles__name"
        ]
        self.test_lookups(LOOKUPS, qs)


