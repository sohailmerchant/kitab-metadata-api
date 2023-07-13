from argparse import Namespace
from operator import truediv
from rest_framework import serializers
from .models import personName, textMeta, authorMeta,versionMeta, AggregatedStats, relationType, a2bRelation
from rest_flex_fields import FlexFieldsModelSerializer

import re

'''
Using drf-flex-fields app to select particular fields which allows fields to be expanded
https://github.com/rsinger86/drf-flex-fields
'''
class personNameSerializer(FlexFieldsModelSerializer):
    
    class Meta:        
        
        model = personName
        fields = ("author_id", "language","shuhra","ism", "nasab", "kunya", "laqab", "nisba")
        #fields = ("__all__")
        depth=0



class ShallowVersionSerializer(FlexFieldsModelSerializer):
    """This serializer is used to serialize the version metadata in text and author queries
    (it excludes the author and text metadata)"""
    class Meta:        
        model = versionMeta
        fields = ("__all__")
        depth=0  # exclude text and author metadata

class RelationTypeSerializer(FlexFieldsModelSerializer):
    class Meta:        
        model = relationType
        fields = ("__all__")
        #depth=0    

class AllRelationSerializer(FlexFieldsModelSerializer):
    #text_a_uri = serializers.ReadOnlyField(source="text_a_id.text_uri")
    #text_b_uri = serializers.ReadOnlyField(source="text_b_id.text_uri")
    
    class Meta:        
        model = a2bRelation
        fields = ("__all__")
        #fields = ("relation_type",)

        depth=1

    # def to_representation(self, instance):
    #     rep = super().to_representation(instance)
    #     print("+++--------------------------------------------------+++")
    #     print(rep)
    #     print("-----------------------------------------------------")
    #     new_rep = {k:v for k,v in rep.items() if v}
    #     return new_rep

# class RelatedTextSerializer(FlexFieldsModelSerializer):
#     relation_types = RelationTypeSerializer(many=True, read_only=True)

    
#     class Meta:        
#         model = a2bRelation
#         fields = ("text_a_id", "text_b_id")  #, "relation_types")
#         depth=1



# class ShallowTextSerializer(FlexFieldsModelSerializer):

#     class Meta:        
#         model = textMeta
#         fields = ("__all__")
#         #fields = ("text_uri", "title_ar","title_lat","tags", "related_texts", "related_persons")
#         depth=0

# class TextSerializer(FlexFieldsModelSerializer):
# #class TextSerializer(serializers.ModelSerializer):
#     # def get_relations(self): 
#     #     print("get relations:")
#     #     print(a2bRelation.objects.get(text_a_id=self))
#     #     return a2bRelation.objects.get(text_a_id=self)
#     versions = ShallowVersionSerializer(many=True, read_only=True)
#     # versions = serializers.SlugRelatedField(many=True, read_only=True, slug_field='version_uri')
#     #rt = RelatedTextSerializer(source=get_relations, many=True, read_only=True)
#     #rt = AllRelationSerializer(many=True, read_only=True)  # https://stackoverflow.com/a/68892233
#     #rt = serializers.StringRelatedField(many=True)  # this doesn't work at all: 'textMeta' object has no attribute 'rt'
#     #rt = AllRelationSerializer(read_only=True, many=True).data
#     #rt = ShallowTextSerializer(many=True, read_only=True)
#     #related_texts = AllRelationSerializer(source="texts_related", 
#     #                                      many=True, read_only=True)
#     related_texts = serializers.SerializerMethodField()

#     def get_related_texts(self, obj):
#         """obj is a textMeta instance. Returns list of dicts"""
#         qset = a2bRelation.objects.filter(text_a_id=obj)
#         #qset += a2bRelation.objects.filter(text_b_id=obj)
#         return [AllRelationSerializer(m).data for m in qset]

#     class Meta:
#         model = textMeta
#         fields = ("text_uri", "title_ar","title_lat","tags","versions", "related_texts", "related_persons", "texts_related")
#                   #, "texts_related") # (before using "textMeta" instead of "self", and True instead of False for symmetrical, this produces an error: “Field name `texts_related` is not valid for model `textMeta`.”
#         depth=4

class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = textMeta
        fields = ("text_uri", "title_ar", "title_lat", "author_id", "versions", 
                  "related_texts", "related_persons", "tags")
                  #, "texts_related") # (before using "textMeta" instead of "self", and True instead of False for symmetrical, this produces an error: “Field name `texts_related` is not valid for model `textMeta`.”
        #depth=4
        depth=1

    def serialize_text_relations(self, text_instance):
        """Serialize a texts's related texts"""
        # NB: this is probably pretty slow because it's making a db call for each text!

        # list the fields which we want to be present in the serialization:
        side_fields = [
            "text_{}_id_id", "text_{}_id__text_uri", 
            "text_{}_id__title_ar", "text_{}_id__title_lat",
            "text_{}_id__text_type", "text_{}_id__tags"]
        default_fields = [
            "relation_type__code", "start_date", "end_date", "authority", "confidence"]
        
        # get a list of dictionaries containing the desired fields
        # for the situation in which the current text is text A
        # (that is, the first element in the relation triple)
        b_fields = default_fields + [x.format("b") for x in side_fields]
        b_instances = a2bRelation.objects\
            .prefetch_related("text_b_id", "relation_type")\
            .filter(text_a_id=text_instance)\
            .values("relation_type__name", *b_fields)   # queryset will be list of dictionaries instead of model objects!

        # get a list of dictionaries containing the desired fields
        # for the situation in which the current text is text B
        # (that is, the last element in the relation triple)
        a_fields = default_fields + [x.format("a") for x in side_fields] 
        a_instances = a2bRelation.objects\
            .prefetch_related("text_a_id")\
            .filter(text_b_id=text_instance)\
            .values("relation_type__name_inverted", *a_fields)
            # .values("text_a_id_id", "text_a_id__text_uri", 
            #         "text_a_id__title_ar", "text_a_id__title_lat", 
            #         "text_a_id__text_type", "text_a_id__tags",
            #         "relation_type__name_inverted", "relation_type__code", 
            #         "start_date", "end_date", "authority", "confidence"
            #         )

        # format the dictionaries and bring related books from both sides
        # of the relationship into a single list:
        related_books =  []
        for qs in [a_instances, b_instances]:
            for inst in qs:
                d = dict()
                # simplify key names:
                for k in inst:
                    d[re.sub("text_[ab]_id_+|relation_type__|_inverted", "", k)] = inst[k]
                # group the qualifiers of the relation into a separate dictionary:
                d["relation_qualifiers"] = dict()
                for k in ["start_date", "end_date", "authority", "confidence"]:
                    d["relation_qualifiers"][k] = d.pop(k)
                related_books.append(d)

        return related_books
    
    def serialize_person_relations(self, text_instance):
        """Serialize a texts's related persons"""
        # NB: this is probably pretty slow because it's making a db call for each text!

        # list the fields which we want to be present in the serialization:
        side_fields = [
            "person_{}_id_id", "person_{}_id__author_uri", 
            "person_{}_id__author_ar", "person_{}_id__author_lat",
            "person_{}_id__date", "person_{}_id__authorDateString", 
            "person_{}_id__authorDateAH", "person_{}_id__authorDateCE"]
        default_fields = [
            "relation_type__code", "start_date", "end_date", "authority", "confidence"]
        
        # get a list of dictionaries containing the desired fields
        # for the situation in which the current text is text A
        # (that is, the first element in the relation triple)
        b_fields = default_fields + [x.format("b") for x in side_fields]
        b_instances = a2bRelation.objects\
            .prefetch_related("person_b_id", "relation_type")\
            .filter(text_a_id=text_instance)\
            .values("relation_type__name", *b_fields)   # queryset will be list of dictionaries instead of model objects!

        # get a list of dictionaries containing the desired fields
        # for the situation in which the current text is text B
        # (that is, the last element in the relation triple)
        a_fields = default_fields + [x.format("a") for x in side_fields] 
        a_instances = a2bRelation.objects\
            .prefetch_related("person_a_id")\
            .filter(text_b_id=text_instance)\
            .values("relation_type__name_inverted", *a_fields)

        # format the dictionaries and bring related books from both sides
        # of the relationship into a single list:
        related_persons =  []
        for qs in [a_instances, b_instances]:
            for inst in qs:
                d = dict()
                # simplify key names:
                for k in inst:
                    d[re.sub("person_[ab]_id_+|relation_type__|_inverted", "", k)] = inst[k]
                # group the qualifiers of the relation into a separate dictionary:
                d["relation_qualifiers"] = dict()
                for k in ["start_date", "end_date", "authority", "confidence"]:
                    d["relation_qualifiers"][k] = d.pop(k)
                related_persons.append(d)

        return related_persons



    def to_representation(self, instance):

        rep = super().to_representation(instance)
        # add the text relations to the default representation (__all__ fields):
        rep["related_texts"] = self.serialize_text_relations(instance)
        #rep["related_persons"] = self.serialize_person_relations(instance)
        tags = []
        for tag in rep["tags"].split(" :: "):
            if not tag: 
                continue
            if "born" in tag or "died" in tag or "resided" in tag or "visited" in tag:
                continue
            if "@" in tag:
                tag, source = tag.split("@")
                tags.append({"tag": tag, "source": source})
            else:
                tags.append({"tag": tag, "source": None})
        rep["tags"] = tags
        return rep
    
class ShallowTextSerializer(TextSerializer):
    """serialize text model, but without recursion """
    def remove_text_details(self, version_d):
        del version_d["text_id"]
        return version_d

    def to_representation(self, instance):
        # run the normal text serializer:
        rep = super().to_representation(instance)
        rep["versions"] = [self.remove_text_details(v) for v in rep["versions"]]
        return rep


class AuthorMetaSerializer(FlexFieldsModelSerializer):
    #texts = serializers.SlugRelatedField(many=True, read_only=True, slug_field='text_uri')
    #versions = serializers.SlugRelatedField(many=True, read_only=True, slug_field='version_uri')
    texts = TextSerializer(many=True, read_only=True)
    personNames = personNameSerializer(many=True, read_only=True) 

    class Meta:        
        model = authorMeta
        fields = ("id", "author_uri","author_ar", "author_lat","date","authorDateAH","authorDateCE","authorDateString","personNames","texts")
        depth=3



class VersionMetaSerializer(FlexFieldsModelSerializer):
#class VersionMetaSerializer(serializers.ModelSerializer):
    """This serializer is used to serialize the version metadata in version queries,
    and includes the text and author metadata"""
    # author_names = personNameSerializer(many=True, read_only=True)  
    # author = personNameSerializer(many=True, read_only=True)
    text_id = TextSerializer()
    
    #author_meta = AuthorMetaSerializer(many=False, read_only=True)
    
    class Meta:
        
        model = versionMeta
        fields = ("version_id", "version_uri", "char_length", "tok_length",
                  "url", "editor", "edition_place", "publisher", "edition_date", "ed_info", 
                  "version_lang", "tags", "status", "annotation_status", "text_id")
        #fields = ("__all__")
        depth=1  # expand text and author metadata

    def to_representation(self, instance):
        # run the normal text serializer:
        rep = super().to_representation(instance)
        # remove the versions field:
        del rep["text_id"]["versions"]
        return rep

class VersionRelatedSerializer(serializers.ModelSerializer):
    related_objects = serializers.SerializerMethodField()

    def get_related_objects(self, obj):
        related_objects = versionMeta.objects.filter()

class AggregatedStatsSerializer(serializers.ModelSerializer):
    class Meta:        
        model = AggregatedStats
        #depth = 1
        fields = ["id","number_of_authors", "number_of_unique_authors","number_of_books","number_of_unique_books","total_word_count","largest_book","date"]