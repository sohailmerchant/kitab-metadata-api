from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["book_id", "book_uri","char_length","tok_length","date","title_ar","title_lat","version_uri","url"]