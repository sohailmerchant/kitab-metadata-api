from rest_framework import serializers
from .models import Book, AggregatedStats
from rest_flex_fields import FlexFieldsModelSerializer

'''
Using drf-flex-fields app to select particular fields whchi allows fields to be expanded
https://github.com/rsinger86/drf-flex-fields
'''
# class BookSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Book
#         fields = ["book_id", "book_uri","char_length","tok_length","date","title_ar","title_lat","version_uri","url"]

class BookSerializer(FlexFieldsModelSerializer):
    class Meta:        
        model = Book
        fields = ("book_id", "book_uri","char_length","tok_length","date","title_ar","title_lat","version_uri","url", "status", "author_lat", "author_ar",'annotation_status')

class AggregatedStatsSerializer(serializers.ModelSerializer):
    class Meta:        
        model = AggregatedStats
        #depth = 1
        fields = ["id","number_of_authors", "number_of_unique_authors","number_of_books","number_of_unique_books","total_word_count","largest_book","date"]