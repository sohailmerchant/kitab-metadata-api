from django.db import models

class authorMeta(models.Model):
    author_uri = models.CharField(max_length=50, unique=True, null=False)
    author_ar = models.CharField(max_length=255,blank=True)
    author_ar_norm = models.CharField(max_length=255,blank=True)   # normalized version of Arabic-script names
    author_lat = models.CharField(max_length=255,blank=True)
    author_lat_norm = models.CharField(max_length=255,blank=True)  # normalized version of Latin-script names
    date = models.IntegerField(null=True,blank=True)
    authorDateAH = models.IntegerField(null=True,blank=True)
    authorDateCE =models.IntegerField(null=True,blank=True)
    authorDateString =models.CharField(max_length=255,blank=True)
    # Create a relationship between two persons (e.g., person A is a student of person B)
    # using a many-to-many field:
    related_persons = models.ManyToManyField(
        "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        through="a2bRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("person_a_id", "person_b_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        symmetrical=False  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    )
    # person_relations = models.ManyToManyField(
    #     "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    #     through="person2personRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
    #     through_fields=("person1_id", "person2_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
    #     symmetrical=False  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    # )

    # Create a relationship between a person and a place (e.g., person was born in place)
    # using a many-to-many field:
    related_places = models.ManyToManyField(
        "placeMeta",  
        through="a2bRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("person_a_id", "place_b_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
    )
    # place_relations = models.ManyToManyField(
    #     "placeMeta",  
    #     through="placeRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
    #     through_fields=("person_id", "place_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
    # )

    # NB: person to text relations are defined in the textMeta model

    
    def __str__(self):
        return self.author_uri

     
class textMeta(models.Model):
    text_uri = models.CharField(max_length=100, unique=True, null=False)
    title_ar = models.CharField(max_length=255,blank=True)
    title_ar_norm = models.CharField(max_length=255,blank=True)  # normalized title
    title_lat = models.CharField(max_length=255,blank=True)
    title_lat_norm = models.CharField(max_length=255,blank=True) # normalized title
    text_type = models.CharField(max_length=10,blank=True)       # document, inscription, ...
    tags = models.CharField(max_length=255,blank=True)
    author_id = models.ForeignKey(authorMeta, related_name='texts', related_query_name="text", on_delete=models.CASCADE)
    # BUT: one text can have more than one author! So, we should rather have:
    #author_id = models.ManyToManyField(authorMeta, 
    #                                   related_name='texts', 
    #                                   related_query_name="text", 
    #                                   on_delete=models.CASCADE)

    # Create a relationship between two texts (e.g., text A is a commentary on text B)
    # using a many-to-many field:
    related_texts = models.ManyToManyField(
        #"self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        "textMeta",
        through="a2bRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("text_a_id", "text_b_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        #symmetrical=True,  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        symmetrical=False,
        related_name="texts_related",
        related_query_name="text_related"
    )
    # text_relations = models.ManyToManyField(
    #     "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    #     through="text2textRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
    #     through_fields=("text1_id", "text2_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
    #     symmetrical=False  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    # )

    # Create a relationship between a text and a person (e.g., text A is a biography of person B)
    # using a many-to-many field:
    related_persons = models.ManyToManyField(
        "authorMeta",  
        through="a2bRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("text_a_id", "person_b_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
    )
    related_places = models.ManyToManyField(
        "placeMeta",  
        through="a2bRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("text_a_id", "place_b_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
    )
        
    def __str__(self):
        return self.text_uri

class personName(models.Model):
   
    language = models.CharField(max_length=3,null=True)
    shuhra = models.CharField(max_length=255,blank=True)
    nasab = models.CharField(max_length=255,blank=True)
    kunya = models.CharField(max_length=255,blank=True)
    ism = models.CharField(max_length=255, blank=True)
    laqab = models.CharField(max_length=255,blank=True)
    nisba = models.CharField(max_length=255,blank=True)
    author_id = models.ForeignKey(authorMeta,related_name='personNames', related_query_name="personName", on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.language
        
class versionMeta(models.Model):
    version_id = models.CharField(max_length=50, unique=True, null=False)
    version_uri = models.CharField(max_length=100,blank=True)
    text_id = models.ForeignKey(textMeta,related_name='versions',related_query_name="version", on_delete=models.CASCADE)
    char_length = models.IntegerField(null=True,blank=True)
    tok_length = models.IntegerField(null=True,blank=True)
    url = models.CharField(max_length=255,blank=True)
    editor = models.CharField(max_length=100,blank=True)
    edition_place = models.CharField(max_length=100,blank=True)
    publisher = models.CharField(max_length=100,blank=True)
    edition_date = models.CharField(max_length=100,blank=True)
    ed_info = models.CharField(max_length=255,blank=True)
    version_lang = models.CharField(max_length=3,blank=True)
    tags = models.CharField(max_length=100,blank=True)
    status = models.CharField(max_length=3,blank=True)
    annotation_status = models.CharField(max_length=50,blank=True)
    
    def __str__(self):
        return self.version_uri

# class regionMeta (models.Model):
#     thurayaURI = models.CharField(max_length=100)
#     name_ar = models.CharField(max_length=100,blank=True)
#     name_lat = models.CharField(max_length=100,blank=True)

#     def __str__(self):
#         return self.person_id + "_" + self.place_id

class placeMeta (models.Model):
    thuraya_uri = models.CharField(max_length=100,blank=True)
    name_ar = models.CharField(max_length=100,blank=True)
    name_lat = models.CharField(max_length=100,blank=True)
    coordinates_str = models.CharField(max_length=50,blank=True) # store as string for now; use geoDjango later?
    # Define relation between places (A is capital of B, place A is in region B, region A is in region B, ...):
    place_relations = models.ManyToManyField(
        "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        through="a2bRelation",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("place_a_id", "place_b_id"),  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        symmetrical=False  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
    )
    #region = models.ManyToManyField(regionMeta,related_name='places',related_query_name="place")
    
    def __str__(self):
        return self.thuraya_uri

class relationType(models.Model):
    name = models.CharField(max_length=50,blank=True)
    name_inverted = models.CharField(max_length=50,blank=True)
    descr = models.CharField(max_length=255,blank=True)
    code = models.CharField(max_length=15,blank=True)
    # the following makes hierarchical structure of relation types possible:
    #parent_type = models.ManyToManyField("self", symmetrical=False, related_name="sub_types", related_query_name="sub_type",)
    entities = models.CharField(max_length=50,blank=True) # person_person, place_place, person_place, ...

    def __str__(self):
        return self.name

# class subRelationType(models.Model):
#     sub_relation_type_id = models.IntegerField(unique=True, null=False)
#     name = models.CharField(max_length=50,blank=True)
#     inverted = models.CharField(max_length=50,blank=True)
#     descr = models.CharField(max_length=255,blank=True)
#     relation_type = models.ForeignKey(relationType, related_name='sub_relations',related_query_name="sub_relation", on_delete=models.CASCADE)
#
#    def __str__(self):
#        return self.sub_relation_name

class a2bRelation (models.Model):
    """Attempt to create a general model for relations between entities.
    
    For text to text relations (A is a commentary on B): fill in text_a_id and text_b_id
    For person to person relations (A is a student of B): fill in person_a_id and person_b_id
    For person to place relations (A was born in B): fill in person_a_id and place_b_id
    for text to person relations (A is a biography of B): fill in text_a_id and person_b_id
    
    """
    # define A and B (pick two, depending on the type of relationship): 
    person_a_id = models.ForeignKey(
        authorMeta,
        related_name="related_persons_a",
        related_query_name="related_person_a",
        on_delete=models.DO_NOTHING,
        null=True, # "null has no effect since there is no way to require a relation at database level": https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        blank=True
        )
    person_b_id = models.ForeignKey(authorMeta,related_name="related_persons_b",related_query_name="related_person_b",
                                    on_delete=models.DO_NOTHING,null=True,blank=True)
    text_a_id = models.ForeignKey(textMeta,related_name="related_texts_a",related_query_name="related_text_a",
                                  on_delete=models.DO_NOTHING,null=True,blank=True)
    text_b_id = models.ForeignKey(textMeta,related_name="related_texts_b",related_query_name="related_text_b",
                                  on_delete=models.DO_NOTHING,null=True,blank=True)
    place_a_id = models.ForeignKey(placeMeta,related_name="related_places_a",related_query_name="related_place_a",
                                   on_delete=models.DO_NOTHING,null=True,blank=True)
    place_b_id = models.ForeignKey(placeMeta,related_name="related_places_b",related_query_name="related_place_b",
                                   on_delete=models.DO_NOTHING,
                                   null=True, 
                                   blank=True)
    #region_id = models.ForeignKey(regionMeta,on_delete=models.DO_NOTHING,null=True,blank=True)
    
    # define the type of relationship between A and B:
    relation_type = models.ForeignKey(relationType,on_delete=models.DO_NOTHING,null=True,blank=True)
    #subRelationType = models.ForeignKey(subRelationType,on_delete=models.DO_NOTHING,null=True,blank=True)

    # additional information about the relationship (data types may need to change!):
    start_date = models.IntegerField(null=True,blank=True)
    end_date = models.IntegerField(null=True,blank=True)
    authority = models.IntegerField(null=True,blank=True)
    confidence = models.IntegerField(null=True,blank=True)
    
# class text2textRelation (models.Model):
#     #text1_id = models.ForeignKey(textMeta,related_name='text1_relations',related_query_name="text1_relation",on_delete=models.DO_NOTHING)
#     #text2_id = models.ForeignKey(textMeta,related_name='text2_relations',related_query_name="text2_relation",on_delete=models.DO_NOTHING)
#     text1_id = models.ForeignKey(textMeta,on_delete=models.DO_NOTHING)
#     text2_id = models.ForeignKey(textMeta,on_delete=models.DO_NOTHING)
#     relationType = models.ForeignKey(relationType,related_name='text_relations',related_query_name="text_relation",on_delete=models.DO_NOTHING)
#     subRelationType = models.ForeignKey(subRelationType,related_name='text_subrelations',related_query_name="text_subrelation",on_delete=models.DO_NOTHING)
    
#     def __str__(self):
#         return self.text1_id + "_" + self.text2_id

# class person2personRelation (models.Model):
#     """Models the relation between two persons (e.g., person1 was a student of person2)"""
#     #person1_id = models.ForeignKey(authorMeta,related_name='person1_relations',related_query_name="person1_relation",on_delete=models.DO_NOTHING)
#     #person2_id = models.ForeignKey(authorMeta,related_name='person2_relations',related_query_name="person2_relation",on_delete=models.DO_NOTHING)
#     person1_id = models.ForeignKey(authorMeta,on_delete=models.DO_NOTHING)
#     person2_id = models.ForeignKey(authorMeta,on_delete=models.DO_NOTHING)
#     relationType = models.ForeignKey(relationType,related_name='person_relations',related_query_name="person_relation",on_delete=models.DO_NOTHING)
#     subRelationType = models.ForeignKey(subRelationType,related_name='person_subrelations',related_query_name="person_subrelation",on_delete=models.DO_NOTHING)
    
#     def __str__(self):
#         return self.person1_id + "_" + self.person2_id

# class placeRelation (models.Model):
#     """Models the relation between a person and a place / region (e.g., person was born in place, person visited place)"""
#     #person_id = models.ForeignKey(authorMeta,related_name='place_relations',related_query_name="place_relation",on_delete=models.DO_NOTHING)
#     person_id = models.ForeignKey(authorMeta,on_delete=models.DO_NOTHING)
#     place_id = models.ForeignKey(placeMeta,related_name='person_relations',related_query_name="person_relation",on_delete=models.DO_NOTHING)
#     region_id = models.ForeignKey(regionMeta,related_name='person_relations',related_query_name="person_relation",on_delete=models.DO_NOTHING)
#     relationType = models.ForeignKey(relationType,related_name='place_relations',related_query_name="place_relation",on_delete=models.DO_NOTHING)
    
#     def __str__(self):
#         return self.person_id + "_" + self.place_id



class AggregatedStats(models.Model):
    id = models.AutoField(primary_key=True)
    number_of_authors = models.IntegerField(null=True)
    number_of_unique_authors = models.IntegerField(null=True,blank=True)
    number_of_books = models.IntegerField(null=True,blank=True)
    number_of_unique_books = models.IntegerField(null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    total_word_count = models.IntegerField(null=True,blank=True)
    largest_book = models.IntegerField(null=True,blank=True)