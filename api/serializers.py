"""
This module contains serializers, whose job it is to map the database response
to a json representation. 

We are using drf-flex-fields app, which (in theory) would allow us to select 
particular fields which allows fields to be selected/omitted/expanded
(https://github.com/rsinger86/drf-flex-fields);
but this functionality has not been put to use yet.

Examples:

version/all/?fields=version_uri,texts
version/all/?omit=id,texts.author
version/all/?expand=organization,friends

In order to be able to expand fields on request, 
the relevant fields must be added to an expandable_fields variable.
Example:

class CountrySerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name', 'population', 'states')
        expandable_fields = {
          'states': (StateSerializer, {'many': True})
        }

TO DO: implement flex fields?
"""

import re
from argparse import Namespace
from operator import truediv
from rest_framework import serializers
from .models import Author, RelationType, A2BRelation, ReleaseInfo, Date, \
                    ObjectName, ObjectNameLink, \
                    Text, Version, ReleaseVersion, SourceCollectionDetails, Edition, \
                    ManuscriptHolding, Place, Manuscript, ExternalID, ExternalIDLink
                    # DateLink, AuthorshipRoleLink, \
                    # CorpusInsights, TextReuseStats, \
                    # GitHubIssue, VersionwiseReuseStats
from rest_flex_fields import FlexFieldsModelSerializer
from django.db.models import Q

####################
# HELPER FUNCTIONS #
####################

def preferred_names_by_language(links):
    """
    Gets the preferred name in each language for a database item
    (if no name has is_preferred in the ObjectNameLink through table,
    use the first name in a language)

    Args:
        links: iterable of ObjectNameLink with .object_name already available

    Returns: 
        {lang: name}
    """
    preferred = {}
    for link in links:
        lang = (link.object_name.language or "und").strip() or "und"
        if lang not in preferred:
            preferred[lang] = link.object_name.name
        else:
            if link.is_preferred:
                preferred[lang] = link.object_name.name
    return preferred

class PreferredNamesByLanguageField(serializers.Field):
    """
    Serializes a `names` field to a dictionary,
    picking only one name per language: {<lang>: <preferred_name>}
    """
    def to_representation(self, value):
        # value might be: instance.object_name_links (RelatedManager)
        links = value.all() if hasattr(value, "all") else value

        return preferred_names_by_language(links)

###############
# SERIALIZERS #
###############

class ExternalIDSerializer(serializers.ModelSerializer):
    #url = serializers.Field()
    url = serializers.SerializerMethodField(read_only=True)
    provider = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    # TODO: add to_representation to make the url field work

    def get_url(self, object):
        return object.url

    class Meta:
        model = ExternalID
        fields = ('provider', 'external_id', 'url')

class ObjectNameSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = ObjectName
        fields = "__all__"


class ShallowPlaceSerializer(serializers.ModelSerializer):
    """Serialize only one name per language"""
    display_names = PreferredNamesByLanguageField(source="object_name_links", read_only=True)
    external_ids = serializers.SerializerMethodField()

    def get_external_ids(self, instance):
        qs = (ExternalIDLink.objects
              .filter(place=instance)
              .select_related("identifier")
        )
        ids = [link.identifier for link in qs]
        return ExternalIDSerializer(ids, many=True, context=self.context).data


    # display_names = serializers.SerializerMethodField()

    # def get_display_names(self, place):
    #     """
    #     Return a dict: { "<lang>": "<best name>" }
    #     where "best name" = preferred name in that language if available,
    #     else the first name in that language.
    #     """
    #     # Pull all name links for this place in one go
    #     links = (
    #         ObjectNameLink.objects
    #         .filter(place=place)
    #         .select_related("object_name")
    #         .order_by(
    #             "object_name__language",     # group by language
    #             "-is_preferred",             # preferred first
    #             "object_name__id"            # stable "first"
    #         )
    #     )

    #     best_by_lang = {}
    #     for link in links:
    #         lang = (link.object_name.language or "und").strip() or "und"
    #         if lang not in best_by_lang:
    #             best_by_lang[lang] = link.object_name.name

    #     return best_by_lang

    class Meta:
        model = Place
        fields = ("id", "code", "display_names", "external_ids") 

class ShallowCountrySerializer(ShallowPlaceSerializer):
    """Serialize only one name per language"""
    class Meta (ShallowPlaceSerializer.Meta):
        fields = ("id", "display_names", "external_ids", "country_code")  # add loc_uri if you have one


class DateSerializer(FlexFieldsModelSerializer):
    # represent foreign keys by their slug instead of numerical key:
    date_type = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    calendar = serializers.SlugRelatedField(read_only=True, slug_field="slug")

    class Meta:
        model = Date
        fields = (
            "id",
            "date_type",
            "calendar",
            "date_str",
            "year",
            "month",
            "day",
            "precision",
            "ce_start",
            "ce_end",
            "source",
            "confidence",
        )
        # make the computed keys impossible to write through the API
        # (can still be written directly from a script, though):
        read_only_fields = ("ce_start", "ce_end")

# BUILDUP: UNCOMMENT:
# class VersionReuseStatsSerializer(FlexFieldsModelSerializer):
#     class Meta:
#         model = VersionwiseReuseStats
#         fields = ('__all__')
#         depth = 0

# BUILDUP: UNCOMMENT:
# class ShallowNameElementsSerializer(serializers.Serializer):
#     """Serializes a queryset of ObjectName objects into:

#     [
#         {
#             "language": "LA",
#             "shuhra": "...",
#             "ism": "...",
#             "nasab": "...",
#             "kunya": "...",
#             "laqab": "...",
#             "nisba": "...",
#         },
#         {
#             "language": "AR",
#             "shuhra": "...",
#             "ism": "...",
#             "nasab": "...",
#             "kunya": "...",
#             "laqab": "...",
#             "nisba": "...",
#         },
#     ]
#     This serializer is used to serialize the name elements in author queries.
#     It excludes the author field. If you want to serialize the ObjectName model,
#     use the ObjectNameSerializer.
#     """

#     # Hardcoded output keys
#     NAME_TYPE_KEYS = ["shuhra", "ism", "nasab", "kunya", "laqab", "nisba"]

#     def to_representation(self, instance):
#         """
#         instance is expected to be:
#         - a queryset
#         - or obj.names.all()
#         """

#         # Group by language
#         grouped = dict()

#         for obj in instance:
#             # Only include recognized name types
#             if obj.name_type in self.NAME_TYPE_KEYS:
#                 lang = obj.language or "und"
#                 RTL = {"ara", "ar", "per", "fa", "urd", "ur"}
#                 if lang.lower() in RTL:
#                     sep = "، "
#                 else:
#                     sep = ", "
#                 # initialize dictionary if it does not exist yet:
#                 if lang not in grouped:
#                     grouped[lang] = {"language": lang}
#                     for key in self.NAME_TYPE_KEYS:
#                         grouped[lang][key] = ""
#                 # add the name to the relevant name type:
#                 name_type = obj.name_type
#                 if grouped[lang][name_type] == "":
#                     grouped[lang][name_type] = obj.name
#                 else: 
#                     grouped[lang][name_type] += sep+obj.name

#         # Return list of language dictionaries
#         return list(grouped.values())

class ShallowEditionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the metadata from the Edition model
    for use in serialization of the Version model 
    (without the foreign key to the Text model).
    Keeps legacy keys: 'editor' and 'edition_date'.
    If you want to serialize the full Edition model, use the EditionSerializer"""
    edition_date = serializers.SerializerMethodField()
    external_ids = serializers.SerializerMethodField()

    def get_external_ids(self, instance):
        qs = (ExternalIDLink.objects
              .filter(edition=instance)
              .select_related("identifier")
        )
        ids = [link.identifier for link in qs]
        return ExternalIDSerializer(ids, many=True, context=self.context).data


    def get_edition_date(self, obj):
        dates = list(
            obj.dates.filter(date_type__slug="edition_date")
                     .values_list("date_str", flat=True)
        )
        return ";".join(dates)
        
    # class Meta:
    #     model = Edition
    #     fields = (
    #         "id",
    #         "editor",
    #         "edition_place",
    #         "publisher",
    #         "edition_date",
    #         "ed_info",
    #         "pdf_url",
    #         "external_ids"
    #     )

    class Meta:
        model = Edition
        # BUILDUP: UNCOMMENT:
        fields = ("id", "editor", "edition_place", "publisher", 
                  "edition_date", "ed_info", "pdf_url", "external_ids")
        depth = 1

# BUILDUP: UNCOMMENT:
# class AuthorshipRoleLinkSerializer(serializers.ModelSerializer):
#     author = ShallowAuthorSerializer(read_only=True)
#     role = serializers.CharField(source="role.slug", read_only=True)

#     class Meta:
#         model = AuthorshipRoleLink
#         fields = ("author", "role", "order", "note")

# BUILDUP: UNCOMMENT:
# class ShallowTextSerializer(FlexFieldsModelSerializer):
#     """This serializer is used to serialize the metadata from the Text model
#     for use in serialization of the Version model 
#     (without the foreign key to the Text model).
#     If you want to serialize the full Text model, use the TextSerializer"""

#     text_type = serializers.SerializerMethodField()
#     author = AuthorshipRoleLinkSerializer(source="authorship_links", many=True, read_only=True)

#     def get_text_type(self, obj):
#         """get a string of comma-separated text types"""
#         slugs = obj.text_types.values_list("slug", flat=True)
#         flat_slugs = []
#         for slug in re.split(" *[,:،] *", slugs):
#             if slug and slug not in flat_slugs:
#                 flat_slugs.append(slug)
#         return " :: ".join(sorted(flat_slugs))
    
#     def get_author(self, obj):
#         """get a list of """

    
#     class Meta:
#         model = Text
#         fields = (
#             "id", 
#             "text_uri", 
#             "author", 
#             "titles_ar", 
#             "titles_lat", 
#             "title_ar_prefered", 
#             "title_lat_prefered",
#             "text_type", 
#             "tags", 
#             "bibliography", 
#             "notes")
#         depth = 1


class ShallowVersionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in text and author queries
    (it excludes the author and text metadata)"""
    edition = ShallowEditionSerializer(read_only=True)

    def serialize_relations(self, version_instance):
        """serialize a version's parts 
        (for books split into pieces because of their length, like BiharAnwar)"""
        # select the versions that are part of the current version_instance:
        parts = Version.objects\
            .filter(part_of__version_uri=version_instance.version_uri)
        return {"parts": parts}
        # # get the bookwise text reuse statistics: 
        # version_reuse_stats = VersionwiseReuseStats.objects\
        #     .filter(release_version__version__version_uri=version_instance.version_uri)\
        #     .first()
        # try:
        #     return {"parts": sorted(list(set([d.version_uri for d in parts]))), 
        #             "n_reuse_instances": version_reuse_stats.n_instances,
        #             "n_reuse_versions": version_reuse_stats.n_versions
        #             }
        # except:
        #     return {"parts": sorted(list(set([d.version_uri for d in parts]))), 
        #             "n_reuse_instances": 0,
        #             "n_reuse_versions": 0
        #             }

    def to_representation(self, instance):
        """Customize the default json representation"""
        # get the default representation:
        json_rep = super().to_representation(instance)
        # use only the release code instead of the full release version dictionary:
        release_codes = [d["release_info"]["release_code"] for d in json_rep.pop("release_versions")]
        releases = {"releases": release_codes}
        # add the version URIs of the parts: 
        reverse_foreign_keys = self.serialize_relations(instance)
        # use only the version URI for the part_of key:
        part_of = json_rep.pop("part_of")
        try:
            part_of = {"part_of": part_of["version_uri"]}
        except:
            part_of = {"part_of": None}

        return {**json_rep, **reverse_foreign_keys, **part_of, **releases}

    class Meta:
        model = Version
        fields = ("id", "version_code", "version_uri", "edition", "language", "release_versions", "part_of", "parts")
        depth = 2  


class ShallowManuscriptSerializer(FlexFieldsModelSerializer):
    transcriptions = ShallowVersionSerializer(many=True, read_only=True)

    def serialize_titles(self, ms_instance):
        """
        Create key-value pairs for the manuscript's titles;
        """
        data = {
            "titles": []
        }

        links = (
            ms_instance.object_name_links
            .select_related("object_name")
            .all()
        )

        if not links:
            return data
        
        for link in links:
            n = link.object_name
            if not n.name:
                continue

            # Add the title data:
            data["titles"].append({
                "title": n.name,
                "normalized_title": n.normalized_name,
                "title_type": n.name_type,
                "language": n.language,
                "is_preferred": link.is_preferred,
                "source": link.source
            })

        return data

    def serialize_dates(self, ms_instance):
        """Create key-value pairs for dates related to the manuscript"""
        data = {"dates": []}

        # get a full list of date dictionaries:
        dates_qs = ms_instance.dates.select_related("date_type", "calendar").all()
        
        data["dates"] = DateSerializer(dates_qs, many=True, context=self.context).data

        return data

    def to_representation(self, instance):
        """Override the default json representation"""

        # make the default serialization:
        json_rep = super().to_representation(instance)

        # add the titles to the default representation:
        try:
            json_rep = {**json_rep, **self.serialize_titles(instance)}
        except Exception as e:
            print("Error adding titles:", e)

        
        # add the dates to the default representation:
        try:
            json_rep = {**json_rep, **self.serialize_dates(instance)}
        except Exception as e:
            print("Error adding dates:", e)


        return json_rep

    class Meta:
        model = Manuscript
        fields = ("manuscript_uri", 
                  "tags", "bibliography", "notes", "transcriptions")
        depth = 1



class ShallowManuscriptHoldingSerializer(FlexFieldsModelSerializer):
    country = ShallowCountrySerializer(read_only=True)
    city = ShallowPlaceSerializer(read_only=True)
    names = PreferredNamesByLanguageField(source="object_name_links", read_only=True)

    # def serialize_names(self, instance):
    #     """
    #     Serialize all related ObjectNames.
    #     """
    #     names = instance.names.all()

    #     return {
    #         "names": ShallowObjectNameSerializer(
    #             names,
    #             many=True,
    #             context=self.context
    #         ).data
    #     }

    # def to_representation(self, instance):
    #     json_rep = super().to_representation(instance)

    #     try:
    #         json_rep = {
    #             **json_rep,
    #             **self.serialize_names(instance)
    #         }
    #     except Exception as e:
    #         print("ERROR serializing names in ManuscriptHolding:", e)

    #     return json_rep

    class Meta:
        model = ManuscriptHolding
        fields = (
            "names",
            "loc_uri",
            "country",
            "city"
        )

# BUILDUP: UNCOMMENT:
# class PersonNameSerializer(FlexFieldsModelSerializer):
#     """This serializer is used to serialize the full PersonName model.
#     If you want to exclude the author: use the ShallowNameElementsSerializer."""

#     class Meta:
#         model = ObjectName
#         fields = ("language", "name", "normalized_name", "name_type")
#         depth = 0


class RelationTypeSerializer(FlexFieldsModelSerializer):
    
    class Meta:
        model = RelationType
        fields = ("__all__")
        # depth=0


class AllRelationsSerializer(FlexFieldsModelSerializer):

    def to_representation(self, instance):
        """Override the default json representation"""
        # get the default json representation:
        json_rep = super().to_representation(instance)
        # remove unwanted keys in the dictionary:
        # BUILDUP: UNCOMMENT:
        for k in ["person_a", "person_b", "place_a", "place_b", "text_a", "text_b"]:
            for field in ["related_persons", "related_places", "related_texts", "author"]:
                try: 
                    del json_rep[k][field]
                except Exception as e:
                    pass
        return json_rep

    class Meta:
        model = A2BRelation
        fields = ("__all__")
        depth = 2

class AllRelationTypesSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = RelationType
        fields = ("__all__")
        depth = 2

class TextSerializer(FlexFieldsModelSerializer):
    include_author = True
    include_related_texts = True
    include_related_persons = True
    include_related_places = True
    versions = ShallowVersionSerializer(many=True, read_only=True)
    external_ids = serializers.SerializerMethodField()

    def get_external_ids(self, text_instance):
        qs = (ExternalIDLink.objects
              .filter(text=text_instance)
              .select_related("identifier")
        )
        ids = [link.identifier for link in qs]
        return ExternalIDSerializer(ids, many=True, context=self.context).data

    def serialize_titles(self, text_instance):
        """
        Create key-value pairs for the book's titles;
        (including old keys: titles_ar, titles_lat, 
        title_ar_prefered, title_lat_prefered)
        """
        data = {
            "titles_ar": "",
            "titles_lat": "",
            "title_ar_prefered": "",
            "title_lat_prefered": "",
            "titles": []
        }

        links = (
            text_instance.object_name_links
            .select_related("object_name")
            .all()
        )

        if not links:
            return data
        
        for link in links:
            n = link.object_name
            if not n.name:
                continue

            # Add the title data:
            data["titles"].append({
                "title": n.name,
                "normalized_title": n.normalized_name,
                "title_type": n.name_type,
                "language": n.language,
                "is_preferred": link.is_preferred,
                "source": link.source
            })
            
            # define which legacy script key the name should be stored under:
            lang = (n.language or "und").upper()
            if lang and lang[:2] in ("AR", "UR", "PE", "FA"):
                script_key = "titles_ar"
                preferred_key = "title_ar_prefered"
                sep = " :: " # "، "
            else:
                script_key = "titles_lat"
                preferred_key = "title_lat_prefered"
                sep = " :: " # ", "

            # store the name to the relevant script key:
            if not data[script_key]:
                data[script_key] = n.name
            elif n.name not in data[script_key].split(", "):
                data[script_key] += sep + n.name
    
            # if the name is the preferred name, store it there, too:
            if link.is_preferred:
                if not data[preferred_key]:
                    data[preferred_key] = n.name
                elif n.name not in data[preferred_key].split(", "):
                    data[preferred_key] += sep + n.name

        return data

    def serialize_relations(self, text_instance):
        """serialize a text's relations"""
        # get all relationships in which the current text is involved:
        relationship_instances = A2BRelation.objects\
            .select_related("relation_type", "person_a", "person_b", "text_a", "text_b", "place_a", "place_b")\
            .filter(Q(text_a=text_instance) | Q(text_b=text_instance))
        # NB: select_related creates a more complex SQL query that joins the relevant tables,
        # so that the foreign-key relationships are included in the query set
        # and no further database lookups are needed to get attributes from the foreign-key related table 
        # (see https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-related)

        # divide these relations into the relevant categories:

        related_persons = []
        related_texts = []
        authors = []
        related_places = []
        for d in relationship_instances:

            # create a new dictionary in which we only collect the relevant fields:
            
            new_d = dict(
                relation_type_code=d.relation_type.code,
                relation_subtype_code=d.relation_type.subtype_code,
                # BUILDUP: UNCOMMENT:
                #start_date_AH=d.start_date_AH,
                #end_date_AH=d.end_date_AH,
                authority=d.authority,
                confidence=d.confidence
            )

            # add relevant fields for each type of relation:
            if d.text_a and d.text_b:
                # BUILDUP: UNCOMMENT:
                # # delete keys irrelevant to book-to-book relations:
                # del new_d["start_date_AH"]
                # del new_d["end_date_AH"]
                # add only the information about the related book:
                if d.text_a.text_uri == text_instance.text_uri:
                    new_d["relation_type_name"] = d.relation_type.name
                    new_d["related_text_uri"] = d.text_b.text_uri
                else:
                    new_d["relation_type_name"] = d.relation_type.name_inverted
                    new_d["related_text_uri"] = d.text_a.text_uri
                related_texts.append(new_d)
            elif d.person_a or d.person_b:
                # BUILDUP: UNCOMMENT:
                # # remove keys irrelevant to book-person relation:
                # del new_d["start_date_AH"]
                # del new_d["end_date_AH"]
                # add the relevant relation_type_name:
                if d.person_a:
                    new_d["related_person_uri"] = d.person_a.author_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                    person_obj = d.person_a
                else: 
                    new_d["related_person_uri"] = d.person_b.author_uri
                    new_d["relation_type_name"]= d.relation_type.name
                    person_obj = d.person_b
                if d.relation_type.code == "AUTH":
                    if self.include_author:
                        auth_d = ShallowAuthorSerializer(person_obj, context=self.context).data
                        authors.append(auth_d)
                        #authors.append(d.person_b.author_uri)
                    continue
                related_persons.append(new_d)
            elif d.place_a or d.place_b:
                if d.place_a:
                    new_d["related_place_id"] = d.place_a.id
                    new_d["related_place_name"] = d.place_a.names.first()
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else: 
                    new_d["related_place_id"] = d.place_b.id
                    new_d["related_place_name"] = d.place_b.names.first()
                    new_d["relation_type_name"]= d.relation_type.name
                related_places.append(new_d)

        # combine the categories into a dictionary that will be added to the json representation:
        d =  dict()
        if self.include_related_texts:
            d["related_texts"] = related_texts
        if  self.include_related_persons:
            d["related_persons"] = related_persons
        if  self.include_related_places:
            d["related_places"] = related_places
        if self.include_author:
            d["author"] = authors
        return d

    def to_representation(self, instance):
        """Override the default json representation"""

        # make the default serialization:
        json_rep = super().to_representation(instance)

        # # remove the "texts" list nested within author:
        # try: # deal with the situation in which the user doesn't request the "author" field:
        #     for i in range(len(json_rep["author"])):
        #         del json_rep["author"][i]["texts"]
        # except Exception as e:
        #     print(e)

        # add the titles to the default representation:
        try:
            json_rep = {**json_rep, **self.serialize_titles(instance)}
        except Exception as e:
            print("Error adding titles:", e)

        # add the relationships to the default representation (__all__ fields):
        try:
            json_rep = {**json_rep, **self.serialize_relations(instance)}
        except Exception as e:
            print("Error adding book relations:", e)

        return json_rep

    class Meta:
        model = Text
        # TODO: add text types
        fields = ("text_uri", "tags", "bibliography", "versions", "external_ids")
        depth = 1

class ShallowTextSerializer(TextSerializer):
    include_author = False
    include_related_texts = True
    include_related_persons = True
    include_related_places = True

# class VersionReleaseListSerializer(FlexFieldsModelSerializer):
#     """This serializer is used to get a list of all releases a version is present in"""

#     def serialize_release_list(self, release_instance):
#         print("release_instance", release_instance)
#         print("----------------------------------------------------------")
#         print("release_instance.id:", release_instance.id)
#         # release_detail_instances = ReleaseInfo.objects\
#         #     .filter(release_code=release_instance.release_info.release_code)
#         # release_list = [d.release_code for d in release_detail_instances]
#         # print(release_list)
#         # return release_list
#         release_code = ReleaseInfo.objects\
#             .get(release_code=release_instance.release_info.release_code).release_code
#         return release_code
        
#     def to_representation(self, instance):
#         return self.serialize_release_list(instance)

#     class Meta:
#         model = ReleaseVersion

class VersionReleaseListSerializer(FlexFieldsModelSerializer):
    """This serializer is used to get a list of all releases a version is present in
    
    NOT USED???"""

    def serialize_release_list(self, release_instance):
        release_code = ReleaseInfo.objects.get(release_code=release_instance.release_info.release_code).release_code
        return release_code
        
    def to_representation(self, instance):
        return self.serialize_release_list(instance)

    class Meta:
        model = ReleaseVersion


class ShallowReleaseVersionSerializer(FlexFieldsModelSerializer):

    def to_representation(self, instance):
        json_rep = super().to_representation(instance)
        try:
            release_meta = json_rep["release_info"]

            del release_meta["id"]
            del release_meta["release_notes"]
            del json_rep["release_info"]
            del json_rep["id"]
            del json_rep["version"]
            return {**release_meta, **json_rep}
        except Exception as e:
            print("ShallowReleaseVersionSerializer error:", e)
            print(json_rep)
            return json_rep

    class Meta:
        model = ReleaseVersion
        #fields = ('__all__')
        fields = ("id", "char_length", "tok_length", "url", "analysis_priority", 
                  "annotation_status", "tags", "notes", "release_info", "version")
        depth=1



class ManuscriptHoldingSerializer(FlexFieldsModelSerializer):
    country = ShallowCountrySerializer(read_only=True)
    city = ShallowPlaceSerializer(read_only=True)
    names = PreferredNamesByLanguageField(source="object_name_links", read_only=True)
    manuscripts = ShallowManuscriptSerializer(many=True, read_only=True)
    external_ids = serializers.SerializerMethodField()

    def get_external_ids(self, instance):
        qs = (ExternalIDLink.objects
              .filter(manuscript_holding=instance)
              .select_related("identifier")
        )
        ids = [link.identifier for link in qs]
        return ExternalIDSerializer(ids, many=True, context=self.context).data


    # def serialize_names(self, instance):
    #     """
    #     Serialize all related ObjectNames.
    #     """
    #     names = instance.names.all()

    #     return {
    #         "names": ShallowObjectNameSerializer(
    #             names,
    #             many=True,
    #             context=self.context
    #         ).data
    #     }

    # def to_representation(self, instance):
    #     json_rep = super().to_representation(instance)

    #     try:
    #         json_rep = {
    #             **json_rep,
    #             **self.serialize_names(instance)
    #         }
    #     except Exception as e:
    #         print("ERROR serializing names in ManuscriptHolding:", e)

    #     return json_rep

    class Meta:
        model = ManuscriptHolding
        fields = (
            "id",
            "names",
            "loc_uri",
            "country",
            "city",
            "notes",
            "manuscripts", 
            "external_ids"
        )

class ManuscriptSerializer(FlexFieldsModelSerializer):
    include_related_texts = True
    include_related_persons = True
    include_related_places = True
    include_related_manuscripts = True
    include_related_editions = True
    transcriptions = ShallowVersionSerializer(many=True, read_only=True)
    manuscript_holding = ShallowManuscriptHoldingSerializer()
    external_ids = serializers.SerializerMethodField()

    def get_external_ids(self, instance):
        qs = (ExternalIDLink.objects
              .filter(manuscript=instance)
              .select_related("identifier")
        )
        ids = [link.identifier for link in qs]
        return ExternalIDSerializer(ids, many=True, context=self.context).data


    def serialize_titles(self, ms_instance):
        """
        Create key-value pairs for the manuscript's titles;
        """
        data = {
            "titles": []
        }

        links = (
            ms_instance.object_name_links
            .select_related("object_name")
            .all()
        )

        if not links:
            return data
        
        for link in links:
            n = link.object_name
            if not n.name:
                continue

            # Add the title data:
            data["titles"].append({
                "title": n.name,
                "normalized_title": n.normalized_name,
                "title_type": n.name_type,
                "language": n.language,
                "is_preferred": link.is_preferred,
                "source": link.source
            })

        return data

    def serialize_dates(self, ms_instance):
        """Create key-value pairs for dates related to the manuscript"""
        data = {"dates": []}

        # get a full list of date dictionaries:
        dates_qs = ms_instance.dates.select_related("date_type", "calendar").all()
        
        data["dates"] = DateSerializer(dates_qs, many=True, context=self.context).data

        return data

    def serialize_relations(self, ms_instance):
        """serialize a manuscript's relations"""
        # get all relationships in which the current manuscript is involved:
        relationship_instances = A2BRelation.objects\
            .select_related("relation_type", "person_a", "person_b", "text_a", "text_b", 
                            "place_a", "place_b", "manuscript_a", "manuscript_b",
                            "edition_a", "edition_b",)\
            .filter(Q(manuscript_a=ms_instance) | Q(manuscript_b=ms_instance))
        # NB: select_related creates a more complex SQL query that joins the relevant tables,
        # so that the foreign-key relationships are included in the query set
        # and no further database lookups are needed to get attributes from the foreign-key related table 
        # (see https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-related)

        # divide these relations into the relevant categories:

        related_persons = []
        related_texts = []
        related_places = []
        related_manuscripts = []
        related_editions = []
        for d in relationship_instances:

            # create a new dictionary in which we only collect the relevant fields:
            
            new_d = dict(
                relation_type_code=d.relation_type.code,
                relation_subtype_code=d.relation_type.subtype_code,
                # BUILDUP: UNCOMMENT:
                #start_date_AH=d.start_date_AH,
                #end_date_AH=d.end_date_AH,
                authority=d.authority,
                confidence=d.confidence
            )

            # add relevant fields for each type of relation:
            if d.manuscript_a and d.manuscript_b:
                # BUILDUP: UNCOMMENT:
                # # delete keys irrelevant to manuscript-to-manuscript relations:
                # del new_d["start_date_AH"]
                # del new_d["end_date_AH"]
                # add only the information about the related book:
                if d.manuscript_a.manuscript_uri == ms_instance.manuscript_uri:
                    new_d["relation_type_name"] = d.relation_type.name
                    new_d["related_manuscript_uri"] = d.manuscript_b.manuscript_uri
                else:
                    new_d["relation_type_name"] = d.relation_type.name_inverted
                    new_d["related_manuscript_uri"] = d.manuscript_a.manuscript_uri
                related_manuscripts.append(new_d)
            elif d.text_a or d.text_b:
                # BUILDUP: UNCOMMENT:
                # # remove keys irrelevant to manuscript-text relation:
                # del new_d["start_date_AH"]
                # del new_d["end_date_AH"]
                # add the relevant relation_type_name:
                if d.text_a:
                    new_d["related_text_uri"] = d.text_a.text_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else:
                    new_d["related_text_uri"] = d.text_b.text_uri
                    new_d["relation_type_name"]= d.relation_type.name
                related_texts.append(new_d)
            elif d.edition_a or d.edition_b:
                # BUILDUP: UNCOMMENT:
                # # remove keys irrelevant to manuscript-edition relation:
                # del new_d["start_date_AH"]
                # del new_d["end_date_AH"]
                # add the relevant relation_type_name:
                if d.edition_a:
                    new_d["ed_info"] = d.edition_a.ed_info
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else:
                    new_d["ed_info"] = d.edition_b.ed_info
                    new_d["relation_type_name"]= d.relation_type
                related_editions.append(new_d)
            elif d.person_a or d.person_b:
                if d.person_a:
                    new_d["related_person_uri"] = d.person_a.author_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                    person_obj = d.person_a
                else: 
                    new_d["related_person_uri"] = d.person_b.author_uri
                    new_d["relation_type_name"]= d.relation_type.name
                    person_obj = d.person_b
                related_persons.append(new_d)
            elif d.place_a or d.place_b:
                if d.place_a:
                    new_d["related_place_id"] = d.place_a.id
                    new_d["related_place_name"] = d.place_a.names.first()
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else: 
                    new_d["related_place_id"] = d.place_b.id
                    new_d["related_place_name"] = d.place_b.names.first()
                    new_d["relation_type_name"]= d.relation_type.name
                related_places.append(new_d)

        # combine the categories into a dictionary that will be added to the json representation:
        d =  dict()
        if self.include_related_texts:
            d["related_texts"] = related_texts
        if  self.include_related_persons:
            d["related_persons"] = related_persons
        if  self.include_related_places:
            d["related_places"] = related_places
        if  self.include_related_manuscripts:
            d["related_manuscripts"] = related_manuscripts
        if  self.include_related_editions:
            d["related_editions"] = related_editions
        
        return d

    def to_representation(self, instance):
        """Override the default json representation"""

        # make the default serialization:
        json_rep = super().to_representation(instance)

        # add the titles to the default representation:
        try:
            json_rep = {**json_rep, **self.serialize_titles(instance)}
        except Exception as e:
            print("Error adding titles:", e)

        
        # add the dates to the default representation:
        try:
            json_rep = {**json_rep, **self.serialize_dates(instance)}
        except Exception as e:
            print("Error adding dates:", e)

        # add the relationships to the default representation (__all__ fields):
        try:
            json_rep = {**json_rep, **self.serialize_relations(instance)}
        except Exception as e:
            print("Error adding book relations:", e)

        return json_rep

    class Meta:
        model = Manuscript
        fields = ("manuscript_uri", "manuscript_holding", 
                  "tags", "bibliography", "notes", "transcriptions", "external_ids")
        depth = 1



class VersionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in version queries,
    and includes the text and author metadata"""
    text = TextSerializer(read_only=True)
    manuscript = ManuscriptSerializer(read_only=True)
    # BUILDUP: UNCOMMENT:
    edition = ShallowEditionSerializer(read_only=True)
    release_versions = ShallowReleaseVersionSerializer(read_only=True, many=True)
    external_ids = serializers.SerializerMethodField()

    def get_external_ids(self, instance):
        qs = (ExternalIDLink.objects
              .filter(version=instance)
              .select_related("identifier")
        )
        ids = [link.identifier for link in qs]
        return ExternalIDSerializer(ids, many=True, context=self.context).data


    def serialize_relations(self, version_instance):
        """serialize a version's parts 
        (for books split into pieces because of their length, like BiharAnwar)"""
        # select the versions that are part of the current version_instance:
        parts = Version.objects\
            .filter(part_of__version_uri=version_instance.version_uri)
        return {"parts": [d.version.version_uri for d in parts]}
        # # get the bookwise text reuse statistics: 
        # version_reuse_stats = VersionwiseReuseStats.objects\
        #     .filter(release_version__version__version_uri=version_instance.version_uri)\
        #     .first()
        # try:
        #     return {"parts": [d.version.version_uri for d in parts], 
        #             "n_reuse_instances": version_reuse_stats.n_instances,
        #             "n_reuse_versions": version_reuse_stats.n_versions}
        # except:
        #     return {"parts": [d.version.version_uri for d in parts], 
        #             "n_reuse_instances": 0,
        #             "n_reuse_versions": 0
        #             }

    def to_representation(self, instance):
        """Customize the default json representation"""
        # get the default representation:
        json_rep = super().to_representation(instance)

        try:
            # remove the nested list of all versions of the text:
            if "text" in json_rep and json_rep["text"] and "versions" in json_rep["text"]:
                del json_rep["text"]["versions"]
            elif "manuscript" in  json_rep and json_rep["manuscript"] and "transcriptions" in json_rep["manuscript"]:
                del json_rep["manuscript"]["transcriptions"]
            # remove the release_versions dictionary if a specific release was requested:
            release_code = self.context.get('release_code')
            if release_code:
                requested_release = [d for d in json_rep["release_versions"] if d["release_code"] == release_code]
                del json_rep["release_versions"]
                json_rep["release_version"] = requested_release
            # add the version URIs of the parts: 
            parts = self.serialize_relations(instance)
            # use only the version URI for the part_of key:
            part_of = json_rep.pop("part_of")
            try:
                part_of = {"part_of": part_of["version_uri"]}
            except:
                part_of = {"part_of": None}
            
            return {**json_rep, **parts, **part_of}
        except Exception as e:
            print("Error in VersionSerializer: ", e)
            return json_rep

    class Meta:
        model = Version
        #fields = ("__all__")
        #fields = ("id", "version_code", "version_uri", "language", "text", "edition", 
        #          "release_versions", "part_of", "github_issues")
        fields = ("id", "version_code", "version_uri", "language", "text", "manuscript", "edition", 
                  "release_versions", "part_of", "external_ids")
        depth = 3  # expand text and author metadata


class AuthorSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the metadata from the Author model
    (including the related fields).
    If you want to serialize the Author model without the related fields,
    use the ShallowAuthorSerializer.
    """
    include_authored_texts = True
    include_related_texts = True
    include_related_persons = True
    include_related_places = True
    external_ids = serializers.SerializerMethodField()

    def get_external_ids(self, person_instance):
        qs = (ExternalIDLink.objects
              .filter(author=person_instance)
              .select_related("identifier")
        )
        ids = [link.identifier for link in qs]
        return ExternalIDSerializer(ids, many=True, context=self.context).data

    def serialize_names(self, person_instance):
        """
        Create key-value pairs for the author's name and name elements;
        (including old keys: author_ar, author_lat, 
        author_ar_preferred, author_lat_preferred)
        """
        data = {
            "author_ar": "",
            "author_lat": "",
            "author_ar_prefered": "",
            "author_lat_prefered": "",
            "name_elements": [],
            "full_names": []
        }

        links = (
            person_instance.object_name_links
            .select_related("object_name")
            .all()
        )

        if not links:
            return data
        
        name_elements_keys = ("shuhra", "ism", "nasab", "kunya", "laqab", "nisba")
        name_elements_by_lang = dict()
        full_name_ids = []
        for link in links:
            n = link.object_name
            if not n.name:
                continue
            lang = (n.language or "und").upper()
            if n.name_type == "full_name":
                # avoid duplicating names here
                if n.id in full_name_ids:
                    continue
                full_name_ids.append(n.id)
                data["full_names"].append({
                    "name": n.name,
                    "normalized_name": n.normalized_name,
                    "name_type": n.name_type,
                    "language": n.language,
                    "is_preferred": link.is_preferred,
                    "source": link.source
                    })
                # define which legacy script key the name should be stored under:
                if lang and lang[:2] in ("AR", "UR", "PE", "FA"):
                    script_key = "author_ar"
                    preferred_key = "author_ar_prefered"
                else:
                    script_key = "author_lat"
                    preferred_key = "author_lat_prefered"
                
                # store the name to the relevant script key:
                if not data[script_key]:
                    data[script_key] = n.name
                elif n.name not in data[script_key].split(", "):
                    data[script_key] += ", " + n.name
                
                # if the name is the preferred name, store it there, too:
                if link.is_preferred:
                    if not data[preferred_key]:
                        data[preferred_key] = n.name
                    elif n.name not in data[preferred_key].split(", "):
                        data[preferred_key] += ", " + n.name
            # process the name elements:
            elif n.name_type in name_elements_keys:
                if lang not in name_elements_by_lang:
                    name_elements_by_lang[lang] = {k: [] for k in name_elements_keys}
                if n.name not in name_elements_by_lang[lang][n.name_type]:
                    for el in re.split(" *, *", n.name):
                        if el not in name_elements_by_lang[lang][n.name_type]:
                            name_elements_by_lang[lang][n.name_type].append(el)
            
        for lang, d in name_elements_by_lang.items():
            # convert the list values into comma-separated strings
            d = {k: ", ".join(v) for k,v in d.items()}
            d["language"] = lang
            data["name_elements"].append(d)

        return data

    
    def serialize_dates(self, person_instance):
        """Create key-value pairs for the author's death date
        (date, date_AH, date_CE, date_str) and other related dates (dates)"""
        data = {
            "date": None,
            "date_AH": None,
            "date_CE": None,
            "date_str": "",
        }

        # 1) Full list of date dictionaries
        dates_qs = person_instance.dates.select_related("date_type", "calendar").all()
        data["dates"] = DateSerializer(dates_qs, many=True, context=self.context).data

        # 2) First death_date as a model instance (single query)
        death_dates = (
            person_instance.dates
            .select_related("date_type", "calendar")
            .filter(date_type__slug="death_date")
            .order_by("ce_start", "ce_end", "id")
        )

        if not death_dates:
            return data

        # Legacy keys
        hijri_death = []
        ce_death = []
        for d in death_dates:
            if getattr(d.calendar, "slug", "").lower() in ("hijri", "ah", "qamari"):
                hijri_death.append(d)
            elif getattr(d.calendar, "slug", "").lower() in ("ce", "gregorian"):
                ce_death.append(d)

        
        if not hijri_death:
            if not ce_death:
                return data
            else:
                ce_death = ce_death[0]
                data["date_str"] = ce_death.date_str or ""
                data["date_CE"] = int(ce_death.ce_start.year)
                # calculate the hijri death date from the CE death date
                data["date_AH"] = int((data["date_CE"]-621.5643) * (33/32))
                data["date"] = data["date_AH"]
        else:
            hijri_death = hijri_death[0]
            data["date_str"] = hijri_death.date_str or ""
            data["date_AH"] = int(hijri_death.year)
            data["date"] = data["date_AH"]
            if ce_death:
                ce_death = ce_death[0]
                data["date_CE"] = int(ce_death.ce_start.year) if ce_death.ce_start else None
            else:
                data["date_CE"] = int(hijri_death.ce_start.year) if hijri_death.ce_start else None

        return data


    def serialize_relations(self, person_instance):
        """serialize a person's relations"""
        if self.include_related_persons == False \
            and self.include_authored_texts == False \
            and self.include_related_texts == False \
            and self.include_related_places == False:
            return {}
        # select the relations in which the current person is involved:
        # BUILDUP: UNCOMMENT:
        # relationship_instances = A2BRelation.objects\
        #     .select_related("relation_type", "person_a", "person_b", "text_a", "text_b", "place_a", "place_b", "manuscript_a", "manuscript_b")\
        #     .filter(Q(person_a=person_instance) | Q(person_b=person_instance))
        relationship_instances = A2BRelation.objects\
            .select_related("relation_type", "person_a", "person_b", "text_a", "text_b", "place_a", "place_b")\
            .filter(Q(person_a=person_instance) | Q(person_b=person_instance))
        
        # NB: select_related creates a more complex SQL query that joins the relevant tables,
        # so that the foreign-key relationships are included in the query set
        # and no further database lookups are needed to get attributes from the foreign-key related table 
        # (see https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-related)

        # divide these relations into the relevant categories:
        
        related_persons = []
        authored_texts = []
        related_texts = []
        related_places = []
        for d in relationship_instances:
            # create a new dictionary in which we only collect the relevant fields:
            new_d = dict(
                relation_type_code=d.relation_type.code,
                relation_subtype_code=d.relation_type.subtype_code,
                # BUILDUP: UNCOMMENT:
                # start_date_AH=d.start_date_AH,
                # end_date_AH=d.end_date_AH,
                authority=d.authority,
                confidence=d.confidence
            )
            # add relevant fields for each type of relation:
            if d.person_a and d.person_b and self.include_related_persons:
                # add only the information about the related person:
                if d.person_a.author_uri == person_instance.author_uri:
                    new_d["relation_type_name"] = d.relation_type.name
                    new_d["related_person_uri"] = d.person_b.author_uri
                else:
                    new_d["relation_type_name"] = d.relation_type.name_inverted
                    new_d["related_person_uri"] = d.person_a.author_uri
                related_persons.append(new_d)
            elif d.text_a or d.text_b and self.include_related_texts:

                # remove keys irrelevant for text relations:
                #del new_d["start_date_AH"]
                #del new_d["end_date_AH"]
                # add the relevant relation_type_name:
                if d.text_a:
                    new_d["related_text_uri"] = d.text_a.text_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                    text_obj = d.text_a
                else: 
                    new_d["related_text_uri"] = d.text_b.text_uri
                    new_d["relation_type_name"]= d.relation_type.name
                    text_obj = d.text_b
                
                if d.relation_type.code == "AUTH":
                    if self.include_authored_texts:
                        text_d = ShallowTextSerializer(text_obj, context=self.context).data
                        authored_texts.append(text_d)
                    continue
                related_texts.append(new_d)
            elif d.place_a or d.place_b:
                if d.place_a:
                    new_d["related_place_id"] = d.place_a.id
                    new_d["related_place_name"] = d.place_a.names.first()
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else: 
                    new_d["related_place_id"] = d.place_b.id
                    new_d["related_place_name"] = d.place_b.names.first()
                    new_d["relation_type_name"]= d.relation_type.name
                related_places.append(new_d)

        # combine the categories into a dictionary that will be added to the json representation:

        d = dict()
        if self.include_related_texts:
            d["related_texts"] = related_texts
        if self.include_authored_texts:
            d["texts"] = authored_texts
        if self.include_related_persons:
            d["related_persons"] = related_persons
        if self.include_related_places:
            d["related_places"] = related_places
        
        return d

    def to_representation(self, instance):
        # create the default json representation of the author metadata
        json_rep = super().to_representation(instance)
        
         # add the date-related keys:
        try:
            json_rep = {**json_rep, **self.serialize_dates(instance)}
        except Exception as e:
            print("ERROR serializing dates in Author model:", e)

        # add the name-related keys:
        try:
            json_rep = {**json_rep, **self.serialize_names(instance)}
        except Exception as e:
            print("ERROR serializing names in Author model:", e)
        
        # add the relationships to the default representation:
        try:
            json_rep = {**json_rep, **self.serialize_relations(instance)}
        except Exception as e:
            print("ERROR serializing relations in Author model:", e)

        # # remove the author dictionary nested inside the texts dictionaries:
        # try:  
        #     for d in json_rep["texts"]:
        #         del d["author"]
        # except Exception as e: # deal with the situation when the user doesn't request the texts
        #     print("No text in the json representation of the Author", e)

        return json_rep
 
    class Meta:
        model = Author
        # BUILDUP: UNCOMMENT:
        # fields = ("id", "author_uri", "author_ar", "author_ar_prefered", 
        #           "author_lat", "author_lat_prefered", "name_elements", 
        #           "texts", "date", "date_AH", "date_CE", "date_str", 
        #           "tags", "bibliography", "notes")
        fields = ("id", "author_uri", "tags", "bibliography", "notes", "external_ids")
        # BUILDUP: UNCOMMENT:
        # depth = 3


class ShallowAuthorSerializer(AuthorSerializer):
    """This serializer is used to serialize the metadata from the Author model
    for use in serialization of the Text model (without the related fields).
    If you want to serialize the full Author model, use the AuthorSerializer.
    """
    include_authored_texts = False
    include_related_texts = True
    include_related_persons = True
    include_related_places = True

    class Meta(AuthorSerializer.Meta):
        fields = ("id", "author_uri", "tags", "bibliography", "notes")



# BUILDUP: UNCOMMENT:
# class CorpusInsightsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CorpusInsights
#         depth = 1

#         fields = ["id", "release_info", "number_of_authors", "number_of_books", "number_of_versions", 
#                   "number_of_pri_versions", "number_of_sec_versions",
#                   "number_of_markdown_versions", "number_of_completed_versions",
#                   "total_word_count", "total_word_count_pri", 
#                   "largest_book", "largest_10_books"]

# BUILDUP: UNCOMMENT:
# class ReleaseCodeOnlySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReleaseInfo
#         fields = ["release_code",]

# BUILDUP: UNCOMMENT:
# class SelectiveVersionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Version
#         fields = ["id", "version_uri"]

# BUILDUP: UNCOMMENT:
# class SelectiveReleaseVersionSerializer(serializers.ModelSerializer):
#     version = SelectiveVersionSerializer(many=False, read_only=True)
#     class Meta:
#         model = ReleaseVersion
#         fields = ["id", "tok_length", "version"]

# BUILDUP: UNCOMMENT:
# class TextReuseStatsSerializerB1(FlexFieldsModelSerializer):
#     """Serialize the text reuse statistics for a single Book1"""
#     release_info = ReleaseCodeOnlySerializer(many=False, read_only=True)

#     def serialize_relations(self, text_reuse_instance):
#         """serialize a text reuse instance with minimal fields"""
#         # version2_instance = Version.objects\
#         #     .select_related("text__author")\
#         #     .get(id=text_reuse_instance.book_2.version.id)

#         # d = {
#         #     "author_ar_prefered": version2_instance.text.author.author_ar_prefered,
#         #     "author_lat_prefered": version2_instance.text.author.author_lat_prefered, 
#         #     "title_ar_prefered": version2_instance.text.title_ar_prefered,
#         #     "title_lat_prefered": version2_instance.text.title_lat_prefered,
#         #     "version_uri": version2_instance.version_uri,
#         #     "tok_length": text_reuse_instance.book_2.tok_length
#         #     }
#         d = {
#             "book2": {
#                 "author_ar_prefered": text_reuse_instance.book_2.version.text.author.author_ar_prefered,
#                 "author_lat_prefered": text_reuse_instance.book_2.version.text.author.author_lat_prefered, 
#                 "title_ar_prefered": text_reuse_instance.book_2.version.text.title_ar_prefered,
#                 "title_lat_prefered": text_reuse_instance.book_2.version.text.title_lat_prefered,
#                 "version_uri": text_reuse_instance.book_2.version.version_uri,
#                 "tok_length": text_reuse_instance.book_2.tok_length
#             }
#         }
#         return d

#     def to_representation(self, instance):
#         # create the default json representation of the author metadata
#         json_rep = super().to_representation(instance)
        
#         # add the relationships to the default representation:
#         try:
#             json_rep = {**json_rep, **self.serialize_relations(instance)}
#         except Exception as e:
#             print(e)
        
#         # replace the full release_info dictionary with only the release_code:
#         try:
#             json_rep["release_code"] = json_rep["release_info"]["release_code"]
#             del json_rep["release_info"]
#         except Exception as e:
#             print(e)
#         return json_rep

#     class Meta:
#         model = TextReuseStats
#         depth = 1
#         fields = ["id", "release_info", "instances_count",
#                   "book1_words_matched", "book2_words_matched", 
#                   "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]

# BUILDUP: UNCOMMENT:
# class ShallowTextReuseStatsSerializer(FlexFieldsModelSerializer):
#     """"""
#     release_info = ReleaseCodeOnlySerializer(many=False, read_only=True)
#     #book_2 = SelectiveReleaseVersionSerializer(many=False, read_only=True)

#     def serialize_relations(self, text_reuse_instance):
#         """serialize a text reuse instance with minimal fields"""
#         version1_instance = Version.objects\
#             .select_related("text__author")\
#             .get(id=text_reuse_instance.book_1.version.id)
#         version2_instance = Version.objects\
#             .select_related("text__author")\
#             .get(id=text_reuse_instance.book_2.version.id)

#         d = {
#             "book1": {
#                 "author_ar_prefered": version1_instance.text.author.author_ar_prefered,
#                 "author_lat_prefered": version1_instance.text.author.author_lat_prefered, 
#                 "title_ar_prefered": version1_instance.text.title_ar_prefered,
#                 "title_lat_prefered": version1_instance.text.title_lat_prefered,
#                 "version_uri": version1_instance.version_uri,
#                 "tok_length": text_reuse_instance.book_1.tok_length
#                 },
#             "book2": {
#                 "author_ar_prefered": version2_instance.text.author.author_ar_prefered,
#                 "author_lat_prefered": version2_instance.text.author.author_lat_prefered, 
#                 "title_ar_prefered": version2_instance.text.title_ar_prefered,
#                 "title_lat_prefered": version2_instance.text.title_lat_prefered,
#                 "version_uri": version2_instance.version_uri,
#                 "tok_length": text_reuse_instance.book_2.tok_length
#                 }
#             }
#         return d

#     def to_representation(self, instance):
#         # create the default json representation of the author metadata
#         json_rep = super().to_representation(instance)
#         # add the relationships to the default representation:
#         try:
#             json_rep = {**json_rep, **self.serialize_relations(instance)}
#         except Exception as e:
#             print(e)
#         # flatten the release_info dictionary:
#         try:
#             json_rep["release_code"] = json_rep["release_info"]["release_code"]
#             del json_rep["release_info"]
#         except Exception as e:
#             print(e)
#         return json_rep

#     class Meta:
#         model = TextReuseStats
#         depth = 1
#         fields = ["id", "release_info", "instances_count",
#                   "book1_words_matched", "book2_words_matched", 
#                   "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]

# BUILDUP: UNCOMMENT:
# class TextReuseStatsSerializer(serializers.ModelSerializer):
#     release_info = ReleaseCodeOnlySerializer(many=False, read_only=True)
#     class Meta:
#         model = TextReuseStats
#         depth = 4
#         fields = ["id", "book_1", "book_2", "release_info", "instances_count",
#                   "book1_words_matched", "book2_words_matched", 
#                   "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]



class ReleaseVersionSerializer(serializers.ModelSerializer):
    """Serializes the ReleaseVersion table in the same way as the
    VersionSerializer does. This is necessary because release-version-
    specific metadata cannot be reliably filtered starting from the
    Version model for a specific release. 
    E.g., if one filters the versions based on "pri",
    all versions that have "pri" priority in at least one release
    will be returned, even if it has "sec" priority in the 
    requested release. 
    """
    version = VersionSerializer(read_only=True)

    def serialize_relations(self, instance):
        """serialize a version's parts 
        (for books split into pieces because of their length, like BiharAnwar)"""
        # select the versions that are part of the current version_instance:
        parts = ReleaseVersion.objects\
            .filter(version__part_of__version_uri=instance.version.version_uri)
        return {"parts": parts}
        # # get the bookwise text reuse statistics: 
        # version_reuse_stats = VersionwiseReuseStats.objects\
        #     .filter(release_version=instance).first()
        # try:
        #     return {"parts": sorted(list(set([d.version.version_uri for d in parts]))), 
        #             "n_reuse_instances": version_reuse_stats.n_instances,
        #             "n_reuse_versions": version_reuse_stats.n_versions
        #             }
        # except:
        #     return {"parts": sorted(list(set([d.version.version_uri for d in parts]))), 
        #             "n_reuse_instances": 0,
        #             "n_reuse_versions": 0}

    def to_representation(self, instance):
        """Format the result in the same way as the VersionSerializer"""
        json_rep = super().to_representation(instance)
        inverse_foreign_keys = self.serialize_relations(instance)

        # replace the full release_info dictionary with only the release_code:
        try:
            json_rep["release_code"] = json_rep["release_info"]["release_code"]
            json_rep["release_date"] = json_rep["release_info"]["release_date"]
            json_rep["zenodo_link"] = json_rep["release_info"]["zenodo_link"]
        except Exception as e:
            print("Error in ReleaseVersionSerializer:", e)
        # import json
        # print(json.dumps(json_rep, indent=2))
        # extract the relation_version metadata from the result:
        rel_version = {
            "release_code": json_rep["release_code"],
            "release_date": json_rep["release_date"],
            "zenodo_link": json_rep["zenodo_link"],
            "char_length": json_rep["char_length"],
            "tok_length": json_rep["tok_length"],
            "url": json_rep["url"],
            "analysis_priority": json_rep["analysis_priority"],
            "annotation_status": json_rep["annotation_status"],
            "tags": json_rep["tags"],
            "notes": json_rep["notes"],
            **inverse_foreign_keys
        }
        # make the version dictionary the main part of the returned dictionary:
        json_rep = json_rep["version"]

        # insert the release_version metadata into it:
        json_rep["release_version"] = rel_version

        # remove the list with all release versions of this version:
        try:
            del json_rep["release_versions"]
        except Exception as e:
            print("Attempting to remove this key in ReleaseVersionSerializer failed: ", e)

        return json_rep

    class Meta:
        model = ReleaseVersion
        depth = 6
        fields = ("id", "char_length", "tok_length", "url", "analysis_priority", 
                  "annotation_status", "tags", "notes", "release_info", "version")


class ReleaseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseInfo
        depth = 1
        fields = ('__all__')
       
class SourceCollectionDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceCollectionDetails
        depth = 1
        fields = ("__all__")

class EditionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Edition
        depth = 4
        fields = ("__all__")

# BUILDUP: UNCOMMENT:
# class GitHubIssueSerializer(serializers.ModelSerializer):
#     about_author = ShallowAuthorSerializer(read_only=True, many=False)
#     about_text = ShallowTextSerializer(read_only=True, many=False)
#     about_version = ShallowVersionSerializer(read_only=True, many=False)

#     class Meta:
#         model = GitHubIssue
#         depth = 4
#         fields = ("id", "title", "labels", "state", "about_author", "about_text", "about_version")

