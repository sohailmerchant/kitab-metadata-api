from argparse import Namespace
from operator import truediv
from rest_framework import serializers
from .models import authorName, textMeta, authorMeta,versionMeta, AggregatedStats
from rest_flex_fields import FlexFieldsModelSerializer

'''
Using drf-flex-fields app to select particular fields whchi allows fields to be expanded
https://github.com/rsinger86/drf-flex-fields
'''
class AuthorNameSerializer(FlexFieldsModelSerializer):
    
    class Meta:        
        
        model = authorName
        #fields = ("author_uri", "date","author_ar","author_lat")
        fields = ("__all__")
        depth=0

class VersionMetaSerializer(FlexFieldsModelSerializer):
    # author_names = AuthorNameSerializer(many=True, read_only=True)  
    # author = AuthorNameSerializer(many=True, read_only=True)  
    
    class Meta:        
        model = versionMeta
        #fields = ("names")
        fields = ("__all__")
        depth=0

class TextSerializer(FlexFieldsModelSerializer):
    versions = VersionMetaSerializer(many=True, read_only=True)
    # versions = serializers.SlugRelatedField(many=True, read_only=True, slug_field='version_uri')

    class Meta:        
        model = textMeta
        fields = ("text_uri", "title_ar","title_lat","tags","versions", )
        depth=1

class AuthorMetaSerializer(FlexFieldsModelSerializer):
    #texts = serializers.SlugRelatedField(many=True, read_only=True, slug_field='text_uri')
    #versions = serializers.SlugRelatedField(many=True, read_only=True, slug_field='version_uri')
    texts = TextSerializer(many=True, read_only=True)
    author_names = AuthorNameSerializer(many=True, read_only=True) 

    class Meta:        
        model = authorMeta
        fields = ("author_uri","author_ar", "author_lat","date","authorDateAH","authorDateCE","authorDateString","author_names","texts")
        depth=1

class AggregatedStatsSerializer(serializers.ModelSerializer):
    class Meta:        
        model = AggregatedStats
        #depth = 1
        fields = ["id","number_of_authors", "number_of_unique_authors","number_of_books","number_of_unique_books","total_word_count","largest_book","date"]