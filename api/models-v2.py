from django.db import models

class authorMeta(models.Model):
    """Describes a person in the database."""
    author_id = models.CharField(max_length=10, unique=True, null=False)
    author_uri = models.CharField(max_length=50, null=True)
    date = models.CharField(max_length=4,null=True)
    dateAH = models.IntegerField(null=True, blank=True)
    dateCE = models.IntegerField(null=True, blank=True)

    author_ar = models.CharField(max_length=255,null=True)
    author_lat = models.CharField(max_length=255)
    author_ar_prefered = models.CharField(max_length=255, blank=True)
    author_lat_prefered = models.CharField(max_length=255, blank=True)

    related_persons = models.ManyToManyField(
        "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        through="a2bRelation", # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("person_a_id", "person_b_id"), # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        symmetrical=False  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    )
    related_places = models.ManyToManyField(
        "placeMeta",
        through="a2bRelation", 
        through_fields=("person_a_id", "place_b_id"), 
    )

    notes = models.TextField(blank=True)

    # The following fields were moved to the new nameElements table:
    # ism_ar = models.CharField(max_length=255, blank=True)
    # ism_lat = models.CharField(max_length=255,blank=True)
    # kunya_ar = models.CharField(max_length=255,blank=True)
    # kunya_lat = models.CharField(max_length=255,blank=True)
    # laqab_ar = models.CharField(max_length=255,blank=True)
    # laqab_lat = models.CharField(max_length=255,blank=True)
    # nisba_ar = models.CharField(max_length=255,blank=True)
    # nisba_lat = models.CharField(max_length=255,blank=True)
    # shuhra_ar = models.CharField(max_length=255,blank=True)
    # shuhra_lat = models.CharField(max_length=255,blank=True)

    def __str__(self):
        return self.author_uri

class nameElements(models.Model):
    """Describes the elements of a person's name in the database."""
    language = models.CharField(max_length=3, null=True)
    shuhra = models.CharField(max_length=255, blank=True)
    nasab = models.CharField(max_length=255, blank=True)
    kunya = models.CharField(max_length=255, blank=True)
    ism = models.CharField(max_length=255, blank=True)
    laqab = models.CharField(max_length=255, blank=True)
    nisba = models.CharField(max_length=255, blank=True)
    person = models.ForeignKey(authorMeta, related_name='name_elements',
                               related_query_name="name_element", on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.shuhra + "(" + self.person__author_uri + ")"


class textMeta(models.Model):
    """Describes a text in the database."""
    text_id = models.CharField(max_length=10, unique=True, null=False)
    text_uri = models.CharField(max_length=100)
    author_meta = models.ForeignKey(authorMeta, on_delete=models.CASCADE,
                                   related_name='texts', related_query_name="text")
    title_ar = models.CharField(max_length=255)
    title_lat = models.CharField(max_length=255)
    title_ar_prefered = models.CharField(max_length=255, blank=True)
    title_lat_prefered = models.CharField(max_length=255, blank=True)
    text_type = models.CharField(max_length=10, blank=True)
    tags =  models.CharField(max_length=255)

    related_texts = models.ManyToManyField("self", through="a2bRelation", through_fields=("text_a_id", "text_b_id"),
                                           symmetrical=False, related_name="texts_related", related_query_name="text_related")

    related_persons = models.ManyToManyField("authorMeta", through="a2bRelation", through_fields=("text_a_id", "person_b_id"),
                                             related_name="related_texts", related_query_name="related_text")
    related_places = models.ManyToManyField("placeMeta", through="a2bRelation", through_fields=("text_a_id", "place_b_id"),
                                            related_name="related_texts", related_query_name="related_text")

    def __str__(self):
        return self.text_uri

class versionMeta(models.Model):
    """Describes a digital version of a text in the database."""
    version_id = models.CharField(max_length=10, unique=True, null=False)
    version_uri = models.CharField(max_length=100)
    text_meta = models.ForeignKey(textMeta,on_delete=models.CASCADE)
    char_length = models.IntegerField(null=True)
    tok_length = models.IntegerField(null=True)
    url = models.CharField(max_length=255)
    editor = models.CharField(max_length=100,blank=True)
    edition_place = models.CharField(max_length=100,blank=True)
    publisher = models.CharField(max_length=100,blank=True)
    edition_date = models.CharField(max_length=100,blank=True)
    tags = models.CharField(max_length=100,blank=True)
    releases = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return self.version_uri

class placeMeta (models.Model):
    place_id = models.CharField(max_length=10, unique=True, null=False)
    thuraya_uri = models.CharField(max_length=100, blank=True)
    name_ar = models.CharField(max_length=100, blank=True)
    name_lat = models.CharField(max_length=100, blank=True)
    # store as string for now; use geoDjango later?
    coordinates = models.CharField(max_length=50, blank=True)
    # Define relation between places (A is capital of B, place A is in region B, region A is in region B, ...):
    place_relations = models.ManyToManyField(
        "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through="a2bRelation",
        # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        through_fields=("place_a_id", "place_b_id"),
        symmetrical=False  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    )
    # region = models.ManyToManyField(regionMeta,related_name='places',related_query_name="place")

    def __str__(self):
        return self.person_id + "_" + self.place_id


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
    textRelationID = models.IntegerField(unique=True, null=False)
    verion1_Id = models.CharField(max_length=50)
    verion2_Id = models.CharField(max_length=50)
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