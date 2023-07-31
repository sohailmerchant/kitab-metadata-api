from argparse import Namespace
from operator import truediv
from rest_framework import serializers
from .models import personName, textMeta, authorMeta, versionMeta, CorpusInsights, TextReuseStats, ReleaseMeta, relationType, a2bRelation, ReleaseDetails, SourceCollectionDetails
from rest_flex_fields import FlexFieldsModelSerializer

'''
Using drf-flex-fields app to select particular fields which allows fields to be expanded
https://github.com/rsinger86/drf-flex-fields
'''


class personNameSerializer(FlexFieldsModelSerializer):

    class Meta:

        model = personName
        fields = ("author_id", "language", "shuhra", "ism",
                  "nasab", "kunya", "laqab", "nisba")
        #fields = ("__all__")
        depth = 0


class VersionMetaSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in version queries,
    and includes the text and author metadata"""
    # author_names = personNameSerializer(many=True, read_only=True)
    # author = personNameSerializer(many=True, read_only=True)

    class Meta:
        model = versionMeta
        fields = ("__all__")
        depth = 3  # expand text and author metadata


class ShallowVersionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in text and author queries
    (it excludes the author and text metadata)"""
    class Meta:
        model = versionMeta
        fields = ("__all__")
        depth = 0  # exclude text and author metadata


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

# class RelatedTextSerializer(FlexFieldsModelSerializer):
#     relation_types = RelationTypeSerializer(many=True, read_only=True)


#     class Meta:
#         model = a2bRelation
#         fields = ("text_a_id", "text_b_id")  #, "relation_types")
#         depth=1


class TextSerializer(FlexFieldsModelSerializer):
    # def get_relations(self):
    #     print("get relations:")
    #     print(a2bRelation.objects.get(text_a_id=self))
    #     return a2bRelation.objects.get(text_a_id=self)
    versions = ShallowVersionSerializer(many=True, read_only=True)
    # versions = serializers.SlugRelatedField(many=True, read_only=True, slug_field='version_uri')
    #related_txt = RelatedTextSerializer(source=get_relations, many=True, read_only=True)

    class Meta:
        model = textMeta
        fields = ("text_uri", "title_ar", "title_lat", "tags",
                  "versions", "related_texts", "related_persons")
        depth = 1


class AuthorMetaSerializer(FlexFieldsModelSerializer):
    #texts = serializers.SlugRelatedField(many=True, read_only=True, slug_field='text_uri')
    #versions = serializers.SlugRelatedField(many=True, read_only=True, slug_field='version_uri')
    texts = TextSerializer(many=True, read_only=True)
    personNames = personNameSerializer(many=True, read_only=True)

    class Meta:
        model = authorMeta
        fields = ("id", "author_uri", "author_ar", "author_lat", "date",
                  "authorDateAH", "authorDateCE", "authorDateString", "personNames", "texts")
        depth = 3


class CorpusInsightsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorpusInsights
        #depth = 1

        fields = ["id", "number_of_unique_authors", "number_of_books", "number_of_versions",
                  "total_word_count", "largest_book", "total_word_count_pri", "top_10_book_by_word_count"]


class TextReuseStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextReuseStats
        depth = 4
        
        fields = ["id", "book_1", "book_2", "instances_count",
                  "book1_word_match", "book2_word_match"]


class ReleaseMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseMeta
        depth = 6
        fields = ("__all__")

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

