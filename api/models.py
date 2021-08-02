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

