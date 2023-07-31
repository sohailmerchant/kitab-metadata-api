from argparse import Namespace
from operator import truediv
from rest_framework import serializers
from .models import personName, textMeta, authorMeta, versionMeta,\
                    CorpusInsights, TextReuseStats, ReleaseMeta,\
                    relationType, a2bRelation, ReleaseDetails,\
                    SourceCollectionDetails, editionMeta
from rest_flex_fields import FlexFieldsModelSerializer
from django.db.models import Q


'''
Using drf-flex-fields app to select particular fields which allows fields to be expanded
https://github.com/rsinger86/drf-flex-fields
'''



class ShallowNameElementsSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the name elements in author queries.
    It excludes the author_meta field. If you want to serialize the full personName model,
    use hte PersonNameSerializer"""

    class Meta:
        model = personName
        fields = ("language", "shuhra", "ism", "nasab", "kunya", "laqab", "nisba")
        depth = 0


class ShallowEditionMetaSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the metadata from the editionMeta model
    for use in serialization of the versionMeta model 
    (without the foreign key to the textMeta model).
    If you want to serialize the full editionMeta model, use the EditionMetaSerializer"""

    class Meta:
        model = editionMeta
        fields = ("id", "editor", "edition_place", "publisher", 
                  "edition_date", "ed_info", "pdf_url", "worldcat_url")
        depth = 0


class ShallowVersionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in text and author queries
    (it excludes the author and text metadata)"""
    edition_meta = ShallowEditionMetaSerializer(read_only=True)

    class Meta:
        model = versionMeta
        fields = ("id", "version_id", "version_uri", "edition_meta", "language")
        depth = 0  # exclude text and author metadata


class ShallowAuthorMetaSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the metadata from the authorMeta model
    for use in serialization of the textMeta model (without the related fields).
    If you want to serialize the full authorMeta model, use the AuthorMetaSerializer.
    NB: this serializer wraps the author Metadata in a list, 
    in the future we may have multiple authors for a single text"""

    def to_representation(self, instance):
        json_rep = super().to_representation(instance)
        for d in json_rep["texts"]:
            # remove the fields below the text level:
            del d["author_meta"]
            del d["related_texts"]
            del d["related_persons"]
            del d["related_places"]
        return [json_rep]

    class Meta:
        model = authorMeta
        fields = ("id", "author_uri", "author_ar", "author_ar_prefered", 
                  "author_lat", "author_lat_prefered", "name_elements", 
                  "texts", "date", "date_AH", "date_CE", "date_str", "tags", "bibliography", "notes")
        depth = 1


class PersonNameSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the full personName model.
    If you want to exclude the author_meta: use the ShallowNameElementsSerializer."""

    class Meta:
        model = personName
        fields = ("author_meta", "language", "shuhra", "ism",
                  "nasab", "kunya", "laqab", "nisba")
        depth = 0


class RelationTypeSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = relationType
        fields = ("__all__")
        # depth=0


class AllRelationSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = a2bRelation
        fields = ("__all__")
        depth = 2


class TextSerializer(FlexFieldsModelSerializer):
    versions = ShallowVersionSerializer(many=True, read_only=True)
    author_meta = ShallowAuthorMetaSerializer(read_only=True)

    def serialize_relations(self, text_instance):
        """serialize a text's relations"""
        # get all relationships in which the current text is involved:
        relationship_instances = a2bRelation.objects\
            .select_related("relation_type", "person_a", "person_b", "text_a", "text_b", "place_a", "place_b")\
            .filter(Q(text_a=text_instance) | Q(text_b=text_instance))
        # NB: select_related creates a more complex SQL query that joins the relevant tables,
        # so that the foreign-key relationships are included in the query set
        # and no further database lookups are needed to get attributes from the foreign-key related table 
        # (see https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-related)

        # divide these relations into the relevant categories:

        related_persons = []
        related_texts = []
        related_places = []
        for d in relationship_instances:

            # create a new dictionary in which we only collect the relevant fields:
            
            new_d = dict(
                relation_type_code=d.relation_type.code,
                relation_subtype_code=d.relation_type.subtype_code,
                start_date_AH=d.start_date_AH,
                end_date_AH=d.end_date_AH,
                authority=d.authority,
                confidence=d.confidence
            )

            # add relevant fields for each type of relation:

            if d.text_a and d.text_b:
                # add only the information about the related book:
                if d.text_a.text_uri == text_instance.text_uri:
                    new_d["relation_type_name"] = d.relation_type.name
                    new_d["related_text_uri"] = d.text_b.text_uri
                else:
                    new_d["relation_type_name"] = d.relation_type.name_inverted
                    new_d["related_text_uri"] = d.text_a.text_uri
                # delete irrelevant keys:
                del new_d["start_date_AH"]
                del new_d["end_date_AH"]
                related_texts.append(new_d)
            elif d.person_a or d.person_b:
                # add the relevant relation_type_name:
                if d.person_a:
                    new_d["related_person_uri"] = d.person_a.author_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else: 
                    new_d["related_person_uri"] = d.person_b.author_uri
                    new_d["relation_type_name"]= d.relation_type.name
                # remove irrelevant keys:
                del new_d["start_date_AH"]
                del new_d["end_date_AH"]
                related_persons.append(new_d)
            elif d.place_a or d.place_b:
                if d.place_a:
                    new_d["related_place_uri"] = d.place_a.thuraya_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else: 
                    new_d["related_place_uri"] = d.place_b.thuraya_uri
                    new_d["relation_type_name"]= d.relation_type.name
                related_places.append(new_d)

        # combine the categories into a dictionary that will be added to the json representation:
        d =  {
            "related_persons": related_persons, 
            "related_texts": related_texts,
            "related_places": related_places
            }
        return d

    def to_representation(self, instance):

        json_rep = super().to_representation(instance)
        # add the relationships to the default representation (__all__ fields):
        return {**json_rep, **self.serialize_relations(instance)}

    class Meta:
        model = textMeta
        fields = ("text_uri", "title_ar_prefered", "title_lat_prefered", "titles_ar", "titles_lat", "tags", 
                  "versions", "author_meta", "bibliography")
                  #"versions", "related_texts", "related_persons")
        depth = 1



# class VersionReleaseListSerializer(FlexFieldsModelSerializer):
#     """This serializer is used to get a list of all releases a version is present in"""

#     def serialize_release_list(self, release_instance):
#         print("release_instance", release_instance)
#         print("----------------------------------------------------------")
#         print("release_instance.id:", release_instance.id)
#         # release_detail_instances = ReleaseDetails.objects\
#         #     .filter(release_code=release_instance.release.release_code)
#         # release_list = [d.release_code for d in release_detail_instances]
#         # print(release_list)
#         # return release_list
#         release_code = ReleaseDetails.objects\
#             .get(release_code=release_instance.release.release_code).release_code
#         return release_code
        
#     def to_representation(self, instance):
#         return self.serialize_release_list(instance)

#     class Meta:
#         model = ReleaseMeta

# class VersionReleaseListSerializer(FlexFieldsModelSerializer):
#     """This serializer is used to get a list of all releases a version is present in"""

#     def serialize_release_list(self, release_instance):
#         release_code = ReleaseDetails.objects.get(release_code=release_instance.release.release_code).release_code
#         return release_code
        
#     def to_representation(self, instance):
#         return self.serialize_release_list(instance)

#     class Meta:
#         model = ReleaseMeta

class ShallowReleaseSerializer(FlexFieldsModelSerializer):

    def to_representation(self, instance):
        json_rep = super().to_representation(instance)
        release_meta = json_rep["release"]
        del release_meta["id"]
        del json_rep["release"]
        del json_rep["id"]
        del json_rep["version_meta"]

        return {**release_meta, **json_rep}

    class Meta:
        model = ReleaseMeta
        fields = ('__all__')
        depth=1

class VersionMetaSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in version queries,
    and includes the text and author metadata"""
    text_meta = TextSerializer(read_only=True)
    edition_meta = ShallowEditionMetaSerializer(read_only=True)
    releases = ShallowReleaseSerializer(read_only=True, many=True)

    class Meta:
        model = versionMeta
        #fields = ("__all__")
        fields = ("id", "version_id", "version_uri", "releases", "edition_meta", "text_meta", "language")
        depth = 3  # expand text and author metadata


class AuthorMetaSerializer(FlexFieldsModelSerializer):
    texts = TextSerializer(many=True, read_only=True)
    name_elements = ShallowNameElementsSerializer(many=True, read_only=True)

    def serialize_relations(self, person_instance):
        """serialize a person's relations"""
        # select the relations in which the current person is involved:
        relationship_instances = a2bRelation.objects\
            .select_related("relation_type", "person_a", "person_b", "text_a", "text_b", "place_a", "place_b")\
            .filter(Q(person_a=person_instance) | Q(person_b=person_instance))
        # NB: select_related creates a more complex SQL query that joins the relevant tables,
        # so that the foreign-key relationships are included in the query set
        # and no further database lookups are needed to get attributes from the foreign-key related table 
        # (see https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-related)

        # divide these relations into the relevant categories:

        related_persons = []
        related_texts = []
        related_places = []
        for d in relationship_instances:
            # create a new dictionary in which we only collect the relevant fields:
            new_d = dict(
                relation_type_code=d.relation_type.code,
                relation_subtype_code=d.relation_type.subtype_code,
                start_date_AH=d.start_date_AH,
                end_date_AH=d.end_date_AH,
                authority=d.authority,
                confidence=d.confidence
            )
            # add relevant fields for each type of relation:
            if d.person_a and d.person_b:
                # add only the information about the related person:
                if d.person_a.author_uri == person_instance.author_uri:
                    new_d["relation_type_name"] = d.relation_type.name
                    new_d["related_person_uri"] = d.person_b.author_uri
                else:
                    new_d["relation_type_name"] = d.relation_type.name_inverted
                    new_d["related_person_uri"] = d.person_a.author_uri
                related_persons.append(new_d)
            elif d.text_a or d.text_b:
                # add the relevant relation_type_name:
                if d.text_a:
                    new_d["related_text_uri"] = d.text_a.text_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else: 
                    new_d["related_text_uri"] = d.text_b.text_uri
                    new_d["relation_type_name"]= d.relation_type.name
                # remove keys irrelevant for text relations:
                del new_d["start_date_AH"]
                del new_d["end_date_AH"]
                related_texts.append(new_d)
            elif d.place_a or d.place_b:
                if d.place_a:
                    new_d["related_place_uri"] = d.place_a.thuraya_uri
                    new_d["relation_type_name"]= d.relation_type.name_inverted
                else: 
                    new_d["related_place_uri"] = d.place_b.thuraya_uri
                    new_d["relation_type_name"]= d.relation_type.name
                related_places.append(new_d)

        # combine the categories into a dictionary that will be added to the json representation:

        d = {
            "related_persons": related_persons, 
            "related_texts": related_texts,
            "related_places": related_places
            }
        return d

    def to_representation(self, instance):
        # create the default json representation of the author metadata
        json_rep = super().to_representation(instance)
        # add the relationships to the default representation:
        return {**json_rep, **self.serialize_relations(instance)}
 
    class Meta:
        model = authorMeta
        fields = ("id", "author_uri", "author_ar", "author_ar_prefered", 
                  "author_lat", "author_lat_prefered", "name_elements", 
                  "texts", "date", "date_AH", "date_CE", "date_str", "tags", "bibliography", "notes")
        depth = 3


class CorpusInsightsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorpusInsights
        depth = 1

        fields = ["id", "release_info", "number_of_authors", "number_of_books", "number_of_versions", 
                  "number_of_pri_versions", "number_of_sec_versions",
                  "number_of_markdown_versions", "number_of_completed_versions",
                  "total_word_count", "total_word_count_pri", 
                  "largest_book", "largest_10_books"]

class ReleaseCodeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseDetails
        fields = ["release_code",]

class SelectiveVersionMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = versionMeta
        fields = ["id", "version_uri"]

class SelectiveReleaseMetaSerializer(serializers.ModelSerializer):
    version_meta = SelectiveVersionMetaSerializer(many=False, read_only=True)
    class Meta:
        model = ReleaseMeta
        fields = ["id", "tok_length", "version_meta"]

class TextReuseStatsSerializerB1(FlexFieldsModelSerializer):
    """Serialize the text reuse statistics for a single Book1"""
    release = ReleaseCodeOnlySerializer(many=False, read_only=True)

    def serialize_relations(self, text_reuse_instance):
        """serialize a text reuse instance with minimal fields"""
        # version2_instance = versionMeta.objects\
        #     .select_related("text_meta__author_meta")\
        #     .get(id=text_reuse_instance.book_2.version_meta.id)

        # d = {
        #     "author_ar_prefered": version2_instance.text_meta.author_meta.author_ar_prefered,
        #     "author_lat_prefered": version2_instance.text_meta.author_meta.author_lat_prefered, 
        #     "title_ar_prefered": version2_instance.text_meta.title_ar_prefered,
        #     "title_lat_prefered": version2_instance.text_meta.title_lat_prefered,
        #     "version_uri": version2_instance.version_uri,
        #     "tok_length": text_reuse_instance.book_2.tok_length
        #     }
        d = {
            "book2": {
                "author_ar_prefered": text_reuse_instance.book_2.version_meta.text_meta.author_meta.author_ar_prefered,
                "author_lat_prefered": text_reuse_instance.book_2.version_meta.text_meta.author_meta.author_lat_prefered, 
                "title_ar_prefered": text_reuse_instance.book_2.version_meta.text_meta.title_ar_prefered,
                "title_lat_prefered": text_reuse_instance.book_2.version_meta.text_meta.title_lat_prefered,
                "version_uri": text_reuse_instance.book_2.version_meta.version_uri,
                "tok_length": text_reuse_instance.book_2.tok_length
            }
        }
        return d

    def to_representation(self, instance):
        # create the default json representation of the author metadata
        json_rep = super().to_representation(instance)
        # add the relationships to the default representation:
        d = {**json_rep, **self.serialize_relations(instance)}
        d["release"] = d["release"]["release_code"]
        return d

    class Meta:
        model = TextReuseStats
        depth = 1
        fields = ["id", "release", "instances_count",
                  "book1_words_matched", "book2_words_matched", 
                  "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]

class ShallowTextReuseStatsSerializer(FlexFieldsModelSerializer):
    """"""
    release = ReleaseCodeOnlySerializer(many=False, read_only=True)
    #book_2 = SelectiveReleaseMetaSerializer(many=False, read_only=True)

    def serialize_relations(self, text_reuse_instance):
        """serialize a text reuse instance with minimal fields"""
        version1_instance = versionMeta.objects\
            .select_related("text_meta__author_meta")\
            .get(id=text_reuse_instance.book_1.version_meta.id)
        version2_instance = versionMeta.objects\
            .select_related("text_meta__author_meta")\
            .get(id=text_reuse_instance.book_2.version_meta.id)

        d = {
            "book1": {
                "author_ar_prefered": version1_instance.text_meta.author_meta.author_ar_prefered,
                "author_lat_prefered": version1_instance.text_meta.author_meta.author_lat_prefered, 
                "title_ar_prefered": version1_instance.text_meta.title_ar_prefered,
                "title_lat_prefered": version1_instance.text_meta.title_lat_prefered,
                "version_uri": version1_instance.version_uri
                },
            "book2": {
                "author_ar_prefered": version2_instance.text_meta.author_meta.author_ar_prefered,
                "author_lat_prefered": version2_instance.text_meta.author_meta.author_lat_prefered, 
                "title_ar_prefered": version2_instance.text_meta.title_ar_prefered,
                "title_lat_prefered": version2_instance.text_meta.title_lat_prefered,
                "version_uri": version2_instance.version_uri
                }
            }
        return d

    def to_representation(self, instance):
        # create the default json representation of the author metadata
        json_rep = super().to_representation(instance)
        # add the relationships to the default representation:
        json_rep = {**json_rep, **self.serialize_relations(instance)}
        # flatten the release dictionary:
        json_rep["release"] = json_rep["release"]["release_code"]
        return json_rep

    class Meta:
        model = TextReuseStats
        depth = 1
        fields = ["id", "release", "instances_count",
                  "book1_words_matched", "book2_words_matched", 
                  "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]


class TextReuseStatsSerializer(serializers.ModelSerializer):
    release = ReleaseCodeOnlySerializer(many=False, read_only=True)
    class Meta:
        model = TextReuseStats
        depth = 4
        
        fields = ["id", "book_1", "book_2", "release", "instances_count",
                  "book1_words_matched", "book2_words_matched", 
                  "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]

class ReleaseMetaSerializer(serializers.ModelSerializer):
    version_meta = VersionMetaSerializer(read_only=True)

    class Meta:
        model = ReleaseMeta
        depth = 6
        fields = ("id", "char_length", "tok_length", "url", "analysis_priority", 
                  "annotation_status", "tags", "notes", "release", "version_meta")


class ReleaseDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseDetails
        depth = 1
        fields = ('__all__')
       

class SourceCollectionDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceCollectionDetails
        depth = 1
        fields = ("__all__")


class EditionMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = editionMeta
        depth = 4
        fields = ("__all__")