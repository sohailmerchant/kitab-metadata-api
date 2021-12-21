from django.db import models

# Create your models here.
class Book(models.Model):
    book_id = models.CharField(max_length=10, unique=True, null=False)
    book_uri = models.CharField(max_length=100)
    char_length = models.IntegerField(null=True)
    tok_length = models.IntegerField(null=True)
    date = models.CharField(max_length=4)
    title_ar = models.CharField(max_length=255)
    title_lat = models.CharField(max_length=255)
    version_uri = models.CharField(max_length=100)
    url = models.CharField(max_length=255)
    status = models.CharField(max_length=3,null=True)
    author_lat = models.CharField(max_length=255,null=True)
    author_ar = models.CharField(max_length=255,null=True)
    annotation_status = models.CharField(max_length=50, null=True)

class AggregatedStats(models.Model):
    id = models.AutoField(primary_key=True)
    number_of_authors = models.IntegerField(null=True)
    number_of_unique_authors = models.IntegerField(null=True)
    number_of_books = models.IntegerField(null=True)
    number_of_unique_books = models.IntegerField(null=True)
    date = models.DateField(null=True)
    total_word_count = models.IntegerField(null=True)
    largest_book = models.IntegerField(null=True)