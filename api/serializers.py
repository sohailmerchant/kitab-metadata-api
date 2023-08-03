from argparse import Namespace
from operator import truediv
from rest_framework import serializers
from .models import PersonName, Text, Author, Version,\
                    CorpusInsights, TextReuseStats, ReleaseVersion,\
                    RelationType, A2BRelation, ReleaseInfo,\
                    SourceCollectionDetails, Edition
from rest_flex_fields import FlexFieldsModelSerializer
from django.db.models import Q


'''
Using drf-flex-fields app to select particular fields which allows fields to be expanded
https://github.com/rsinger86/drf-flex-fields
'''



class ShallowNameElementsSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the name elements in author queries.
    It excludes the author field. If you want to serialize the full PersonName model,
    use the PersonNameSerializer"""

    class Meta:
        model = PersonName
        fields = ("language", "shuhra", "ism", "nasab", "kunya", "laqab", "nisba")
        depth = 0


class ShallowEditionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the metadata from the Edition model
    for use in serialization of the Version model 
    (without the foreign key to the Text model).
    If you want to serialize the full Edition model, use the EditionSerializer"""

    class Meta:
        model = Edition
        fields = ("id", "editor", "edition_place", "publisher", 
                  "edition_date", "ed_info", "pdf_url", "worldcat_url")
        depth = 1


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
        return {"parts": [d.version_uri for d in parts]}

    def to_representation(self, instance):
        """Customize the default json representation"""
        # get the default representation:
        json_rep = super().to_representation(instance)
        # use only the release code instead of the full release version dictionary:
        release_codes = [d["release_info"]["release_code"] for d in json_rep.pop("release_versions")]
        releases = {"releases": release_codes}
        # add the version URIs of the parts: 
        parts = self.serialize_relations(instance)
        # use only the version URI for the part_of key:
        part_of = json_rep.pop("part_of")
        try:
            part_of = {"part_of": part_of["version_uri"]}
        except:
            part_of = {"part_of": None}

        return {**json_rep, **parts, **part_of, **releases}

    class Meta:
        model = Version
        fields = ("id", "version_code", "version_uri", "edition", "language", "release_versions", "part_of", "parts")
        depth = 2  

class ShallowAuthorSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the metadata from the Author model
    for use in serialization of the Text model (without the related fields).
    If you want to serialize the full Author model, use the AuthorSerializer.
    NB: this serializer wraps the author Metadata in a list, 
    in the future we may have multiple authors for a single text"""
    name_elements = ShallowNameElementsSerializer(many=True, read_only=True)

    def serialize_relations(self, person_instance):
        """serialize a person's relations"""
        # select the relations in which the current person is involved:
        relationship_instances = A2BRelation.objects\
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
        json_rep = super().to_representation(instance)
        #del json_rep["texts"]
        for d in json_rep["texts"]:
            # remove the fields below the text level:
            del d["author"]
            del d["related_texts"]
            del d["related_persons"]
            del d["related_places"]
        json_rep = {**json_rep, **self.serialize_relations(instance)}
        # return the dictionary inside a list (we may have multiple authors later)
        return [json_rep]

    class Meta:
        model = Author
        fields = ("id", "author_uri", "author_ar", "author_ar_prefered", 
                  "author_lat", "author_lat_prefered", "name_elements", 
                  "texts", "date", "date_AH", "date_CE", "date_str", "tags", "bibliography", "notes")
        depth = 1


class PersonNameSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the full PersonName model.
    If you want to exclude the author: use the ShallowNameElementsSerializer."""

    class Meta:
        model = PersonName
        fields = ("author", "language", "shuhra", "ism",
                  "nasab", "kunya", "laqab", "nisba")
        depth = 0


class RelationTypeSerializer(FlexFieldsModelSerializer):
    
    class Meta:
        model = RelationType
        fields = ("__all__")
        # depth=0


class AllRelationSerializer(FlexFieldsModelSerializer):

    def to_representation(self, instance):
        """Override the default json representation"""
        # get the default json representation:
        json_rep = super().to_representation(instance)
        # remove unwanted keys in the dictionary:
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
    versions = ShallowVersionSerializer(many=True, read_only=True)
    author = ShallowAuthorSerializer(read_only=True)

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
        # make the default serialization:
        json_rep = super().to_representation(instance)
        # remove the "texts" list nested within author:
        for i in range(len(json_rep["author"])):
            del json_rep["author"][i]["texts"]
        # add the relationships to the default representation (__all__ fields):
        return {**json_rep, **self.serialize_relations(instance)}

    class Meta:
        model = Text
        fields = ("text_uri", "title_ar_prefered", "title_lat_prefered", "titles_ar", "titles_lat", "tags", 
                  "versions", "author", "bibliography")
                  #"versions", "related_texts", "related_persons")
        depth = 1



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

# class VersionReleaseListSerializer(FlexFieldsModelSerializer):
#     """This serializer is used to get a list of all releases a version is present in"""

#     def serialize_release_list(self, release_instance):
#         release_code = ReleaseInfo.objects.get(release_code=release_instance.release_info.release_code).release_code
#         return release_code
        
#     def to_representation(self, instance):
#         return self.serialize_release_list(instance)

#     class Meta:
#         model = ReleaseVersion

class ShallowReleaseVersionSerializer(FlexFieldsModelSerializer):

    def to_representation(self, instance):
        json_rep = super().to_representation(instance)
        release_meta = json_rep["release_info"]
        del release_meta["id"]
        del release_meta["release_notes"]
        del json_rep["release_info"]
        del json_rep["id"]
        del json_rep["version"]

        return {**release_meta, **json_rep}

    class Meta:
        model = ReleaseVersion
        fields = ('__all__')
        depth=1

class VersionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in version queries,
    and includes the text and author metadata"""
    text = TextSerializer(read_only=True)
    edition = ShallowEditionSerializer(read_only=True)
    release_versions = ShallowReleaseVersionSerializer(read_only=True, many=True)

    def serialize_relations(self, version_instance):
        """serialize a version's parts 
        (for books split into pieces because of their length, like BiharAnwar)"""
        # select the versions that are part of the current version_instance:
        parts = Version.objects\
            .filter(part_of__version_uri=version_instance.version_uri)
        return {"parts": [d.version_uri for d in parts]}

    def to_representation(self, instance):
        """Customize the default json representation"""
        # get the default representation:
        json_rep = super().to_representation(instance)
        # remove the nested list of all versions of the text:
        del json_rep["text"]["versions"]
        # remove the nested list of all texts by the same author: (not necessary anymore: is now already done TextSerializer!)
        #for i in range(len(json_rep["text"]["author"])):
        #    del json_rep["text"]["author"][i]["texts"]
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

    class Meta:
        model = Version
        #fields = ("__all__")
        fields = ("id", "version_code", "version_uri", "language", "text", "edition", "release_versions", "part_of")
        depth = 3  # expand text and author metadata


class AuthorSerializer(FlexFieldsModelSerializer):
    texts = TextSerializer(many=True, read_only=True)
    name_elements = ShallowNameElementsSerializer(many=True, read_only=True)

    def serialize_relations(self, person_instance):
        """serialize a person's relations"""
        # select the relations in which the current person is involved:
        relationship_instances = A2BRelation.objects\
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
        json_rep = {**json_rep, **self.serialize_relations(instance)}
        # remove the author dictionary nested inside the texts dictionaries:
        for d in json_rep["texts"]:
            del d["author"]


        return json_rep
 
    class Meta:
        model = Author
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
        model = ReleaseInfo
        fields = ["release_code",]

class SelectiveVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ["id", "version_uri"]

class SelectiveReleaseVersionSerializer(serializers.ModelSerializer):
    version = SelectiveVersionSerializer(many=False, read_only=True)
    class Meta:
        model = ReleaseVersion
        fields = ["id", "tok_length", "version"]

class TextReuseStatsSerializerB1(FlexFieldsModelSerializer):
    """Serialize the text reuse statistics for a single Book1"""
    release_info = ReleaseCodeOnlySerializer(many=False, read_only=True)

    def serialize_relations(self, text_reuse_instance):
        """serialize a text reuse instance with minimal fields"""
        # version2_instance = Version.objects\
        #     .select_related("text__author")\
        #     .get(id=text_reuse_instance.book_2.version.id)

        # d = {
        #     "author_ar_prefered": version2_instance.text.author.author_ar_prefered,
        #     "author_lat_prefered": version2_instance.text.author.author_lat_prefered, 
        #     "title_ar_prefered": version2_instance.text.title_ar_prefered,
        #     "title_lat_prefered": version2_instance.text.title_lat_prefered,
        #     "version_uri": version2_instance.version_uri,
        #     "tok_length": text_reuse_instance.book_2.tok_length
        #     }
        d = {
            "book2": {
                "author_ar_prefered": text_reuse_instance.book_2.version.text.author.author_ar_prefered,
                "author_lat_prefered": text_reuse_instance.book_2.version.text.author.author_lat_prefered, 
                "title_ar_prefered": text_reuse_instance.book_2.version.text.title_ar_prefered,
                "title_lat_prefered": text_reuse_instance.book_2.version.text.title_lat_prefered,
                "version_uri": text_reuse_instance.book_2.version.version_uri,
                "tok_length": text_reuse_instance.book_2.tok_length
            }
        }
        return d

    def to_representation(self, instance):
        # create the default json representation of the author metadata
        json_rep = super().to_representation(instance)
        # add the relationships to the default representation:
        json_rep = {**json_rep, **self.serialize_relations(instance)}
        json_rep["release_code"] = json_rep["release_info"]["release_code"]
        del json_rep["release_info"]
        return json_rep

    class Meta:
        model = TextReuseStats
        depth = 1
        fields = ["id", "release_info", "instances_count",
                  "book1_words_matched", "book2_words_matched", 
                  "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]

class ShallowTextReuseStatsSerializer(FlexFieldsModelSerializer):
    """"""
    release_info = ReleaseCodeOnlySerializer(many=False, read_only=True)
    #book_2 = SelectiveReleaseVersionSerializer(many=False, read_only=True)

    def serialize_relations(self, text_reuse_instance):
        """serialize a text reuse instance with minimal fields"""
        version1_instance = Version.objects\
            .select_related("text__author")\
            .get(id=text_reuse_instance.book_1.version.id)
        version2_instance = Version.objects\
            .select_related("text__author")\
            .get(id=text_reuse_instance.book_2.version.id)

        d = {
            "book1": {
                "author_ar_prefered": version1_instance.text.author.author_ar_prefered,
                "author_lat_prefered": version1_instance.text.author.author_lat_prefered, 
                "title_ar_prefered": version1_instance.text.title_ar_prefered,
                "title_lat_prefered": version1_instance.text.title_lat_prefered,
                "version_uri": version1_instance.version_uri,
                "tok_length": text_reuse_instance.book_1.tok_length
                },
            "book2": {
                "author_ar_prefered": version2_instance.text.author.author_ar_prefered,
                "author_lat_prefered": version2_instance.text.author.author_lat_prefered, 
                "title_ar_prefered": version2_instance.text.title_ar_prefered,
                "title_lat_prefered": version2_instance.text.title_lat_prefered,
                "version_uri": version2_instance.version_uri,
                "tok_length": text_reuse_instance.book_2.tok_length
                }
            }
        return d

    def to_representation(self, instance):
        # create the default json representation of the author metadata
        json_rep = super().to_representation(instance)
        # add the relationships to the default representation:
        json_rep = {**json_rep, **self.serialize_relations(instance)}
        # flatten the release_info dictionary:
        json_rep["release_code"] = json_rep["release_info"]["release_code"]
        del json_rep["release_info"]
        return json_rep

    class Meta:
        model = TextReuseStats
        depth = 1
        fields = ["id", "release_info", "instances_count",
                  "book1_words_matched", "book2_words_matched", 
                  "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]


class TextReuseStatsSerializer(serializers.ModelSerializer):
    release_info = ReleaseCodeOnlySerializer(many=False, read_only=True)
    class Meta:
        model = TextReuseStats
        depth = 4
        fields = ["id", "book_1", "book_2", "release_info", "instances_count",
                  "book1_words_matched", "book2_words_matched", 
                  "book1_pct_words_matched", "book2_pct_words_matched", "tsv_url"]



class ReleaseVersionSerializer(serializers.ModelSerializer):
    version = VersionSerializer(read_only=True)
    
    def to_representation(self, instance):
        json_rep = super().to_representation(instance)
        # replace the full release_info dictionary with only the release_code:
        json_rep["release_code"] = json_rep["release_info"]["release_code"]
        del json_rep["release_info"]
        # remove the versions dictionary (nested in the text dictionary):
        del json_rep["version"]["text"]["versions"]
        # remove the texts dictionary (nested in the author dictionary):
        for i in range(len(json_rep["version"]["text"]["author"])):
            del json_rep["version"]["text"]["author"][i]["texts"]
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