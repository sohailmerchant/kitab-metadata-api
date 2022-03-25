from operator import truediv
from django.db import models

class authorMeta(models.Model):
    author_uri = models.CharField(max_length=50, unique=True, null=False, primary_key=True)
    author_ar = models.CharField(max_length=255,null=True)
    author_lat = models.CharField(max_length=255)
    date = models.IntegerField(null=True)
    authorDateAH = models.IntegerField(null=True)
    authorDateCE =models.IntegerField(null=True)
    authorDateString =models.CharField(max_length=255,null=True)    
    
    def __str__(self):
        return self.author_uri




      
class textMeta(models.Model):
    text_uri = models.CharField(max_length=100, unique=True, null=False, primary_key=True)
    title_ar = models.CharField(max_length=255)
    title_lat = models.CharField(max_length=255)
    text_type = models.CharField(max_length=10,blank=True)
    tags =  models.CharField(max_length=255)
    author_uri = models.ForeignKey(authorMeta, related_name='texts', related_query_name="text", on_delete=models.CASCADE)
    
    def __str__(self):
        return self.text_uri

class authorName(models.Model):
   
    language = models.CharField(max_length=3,null=True)
    shuhra = models.CharField(max_length=255,blank=True)
    kunya = models.CharField(max_length=255,blank=True)
    ism = models.CharField(max_length=255, blank=True)
    laqab = models.CharField(max_length=255,blank=True)
    nisba = models.CharField(max_length=255,blank=True)
    author_uri = models.ForeignKey(authorMeta,related_name='authornames', related_query_name="authorname", on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.language
        
class versionMeta(models.Model):
    version_id = models.CharField(max_length=50, unique=True, null=False, primary_key=True)
    version_uri = models.CharField(max_length=100)
    text_uri = models.ForeignKey(textMeta,related_name='versions',related_query_name="version", on_delete=models.CASCADE)
    char_length = models.IntegerField(null=True)
    tok_length = models.IntegerField(null=True)
    url = models.CharField(max_length=255)
    editor = models.CharField(max_length=100,blank=True)
    editor_place = models.CharField(max_length=100,blank=True)
    publisher = models.CharField(max_length=100,blank=True)
    edition_date = models.CharField(max_length=100,blank=True)
    ed_info = models.CharField(max_length=255,blank=True)
    version_lang = models.CharField(max_length=3,null=True)
    tags = models.CharField(max_length=100,blank=True)
    status = models.CharField(max_length=3,blank=True)
    annotation_status = models.CharField(max_length=50, null=True)
    
    def __str__(self):
        return self.version_uri



class relationType(models.Model):
    relation_type_id = models.IntegerField(unique=True, null=False)
    relation_name = models.CharField(max_length=50)
    relation_description = models.CharField(max_length=255)
    type = models.CharField(max_length=50)

    def __str__(self):
        return self.relation_name

class subRelationType(models.Model):
    sub_relation_type_id = models.IntegerField(unique=True, null=False)
    sub_relation_name = models.CharField(max_length=50)
    sub_relation_description = models.CharField(max_length=255)
    relationType = models.ForeignKey(relationType,on_delete=models.CASCADE)

    def __str__(self):
        return self.sub_relation_name

class textRelations (models.Model):
    Id1 = models.CharField(max_length=50)
    Id2 = models.CharField(max_length=50)
    relationType = models.ForeignKey(relationType,on_delete=models.DO_NOTHING)
    subRelationType = models.ForeignKey(subRelationType,on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.verion1_Id + "_" + self.version2_Id



class AggregatedStats(models.Model):
    id = models.AutoField(primary_key=True)
    number_of_authors = models.IntegerField(null=True)
    number_of_unique_authors = models.IntegerField(null=True)
    number_of_books = models.IntegerField(null=True)
    number_of_unique_books = models.IntegerField(null=True)
    date = models.DateField(null=True)
    total_word_count = models.IntegerField(null=True)
    largest_book = models.IntegerField(null=True)