from django.db import models


class authorMeta(models.Model):
    """Describes a person in the database."""
    #author_uri = models.CharField(max_length=50, unique=True, null=False)
    author_uri = models.CharField(max_length=50, null=False)
    author_ar = models.CharField(max_length=255, blank=True)
    author_lat = models.CharField(max_length=255, blank=True)
    author_ar_prefered = models.CharField(max_length=255, blank=True)
    author_lat_prefered = models.CharField(max_length=255, blank=True)
    date = models.IntegerField(null=True, blank=True)
    date_AH = models.IntegerField(null=True, blank=True)
    date_CE = models.IntegerField(null=True, blank=True)
    date_str = models.CharField(max_length=255, blank=True)
    tags =  models.CharField(max_length=255, blank=True)
    bibliography = models.TextField(null=False, blank=True)
    notes = models.TextField(null=False, blank=True)

    # Create a relationship between two persons (e.g., person A is a student of person B)
    # using a many-to-many field:
    related_persons = models.ManyToManyField(
        "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        through="a2bRelation", # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("person_a", "person_b"), # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        symmetrical=False,  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        related_name="persons_related",
        related_query_name="person_related"
    )
    # Create a relationship between a person and a place (e.g., person A was born in place B)
    # using a many-to-many field:
    related_places = models.ManyToManyField("placeMeta", through="a2bRelation", through_fields=("person_a", "place_b"), 
                                            related_name="related_persons", related_query_name="related_person")
    # NB: person to text relations are defined in the textMeta model

    def __str__(self):
        return self.author_uri


class textMeta(models.Model):
    """Describes a text in the database."""
    text_uri = models.CharField(max_length=100, unique=True, null=False)
    author_meta = models.ForeignKey(authorMeta, on_delete=models.DO_NOTHING,
                                   related_name='texts', related_query_name="text")
    titles_ar = models.CharField(max_length=255, blank=True)
    titles_lat = models.CharField(max_length=255, blank=True)
    title_ar_prefered = models.CharField(max_length=255, blank=True)
    title_lat_prefered = models.CharField(max_length=255, blank=True)
    text_type = models.CharField(max_length=15, blank=True)  # document, inscription, ...
    tags =  models.CharField(max_length=255, blank=True)
    bibliography = models.TextField(null=False, blank=True)
    notes = models.TextField(null=False, blank=True)

    # Create a relationship between two texts (e.g., text A is a commentary on text B)
    # using a many-to-many field:
    related_texts = models.ManyToManyField("self", through="a2bRelation", through_fields=("text_a", "text_b"),
                                           symmetrical=False, related_name="texts_related", related_query_name="text_related")
    # Create a relationship between a text and a person (e.g., text A is a biography of person B)
    # using a many-to-many field:
    related_persons = models.ManyToManyField("authorMeta", through="a2bRelation", through_fields=("text_a", "person_b"),
                                             related_name="related_texts", related_query_name="related_text")
    # Create a relationship between a text and a place (e.g., text A is a history of place B; text A was written in place B)
    # using a many-to-many field:
    related_places = models.ManyToManyField("placeMeta", through="a2bRelation", through_fields=("text_a", "place_b"),
                                            related_name="related_texts", related_query_name="related_text")

    def __str__(self):
        return self.text_uri


class personName(models.Model):
    """Describes the elements of a person's name in the database."""
    language = models.CharField(max_length=3, blank=False)
    shuhra = models.CharField(max_length=255, blank=True)
    nasab = models.CharField(max_length=255, blank=True)
    kunya = models.CharField(max_length=255, blank=True)
    ism = models.CharField(max_length=255, blank=True)
    laqab = models.CharField(max_length=255, blank=True)
    nisba = models.CharField(max_length=255, blank=True)
    author_meta = models.ForeignKey(authorMeta, related_name='name_elements',
                                    related_query_name="name_element", on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.language


class versionMeta(models.Model):
    """Describes a digital version of a text in the database."""
    version_id = models.CharField(max_length=50, unique=True, null=False)
    version_uri = models.CharField(max_length=100, blank=True)
    text_meta = models.ForeignKey(textMeta, related_name='versions',
                                  related_query_name="version", on_delete=models.DO_NOTHING)
    language = models.CharField(max_length=9, blank=True)
    tags = models.CharField(max_length=100, blank=True)
    edition_meta = models.ForeignKey("editionMeta", related_name='editions',
                                     related_query_name="edition", on_delete=models.DO_NOTHING)
    # NB: - notes, char_lenght, tok length, url, status and annotation status were moved to Release table
    #     - editor, edition_place, publisher, edition_date, ed_info fields were moved to editionMeta model

    def __str__(self):
        return self.version_uri

class editionMeta(models.Model):
    editor = models.CharField(max_length=100, blank=True)
    edition_place = models.CharField(max_length=100, blank=True)
    publisher = models.CharField(max_length=100, blank=True)
    edition_date = models.CharField(max_length=100, blank=True)
    ed_info = models.CharField(max_length=255, blank=True)
    pdf_url = models.CharField(max_length=255, blank=True)
    worldcat_url = models.CharField(max_length=255, blank=True)
    text_meta = models.ForeignKey(textMeta, related_name='editions',
                                  related_query_name="edition", on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.ed_info


class placeMeta (models.Model):
    """Describes a place in the database."""
    thuraya_uri = models.CharField(max_length=100, blank=True)
    name_ar = models.CharField(max_length=100, blank=True)
    name_lat = models.CharField(max_length=100, blank=True)
    # store as string for now; use geoDjango later?
    coordinates_str = models.CharField(max_length=50, blank=True)
    # Define relation between places (A is capital of B, place A is in region B, region A is in region B, ...):
    related_places = models.ManyToManyField("self", through="a2bRelation", through_fields=("place_a", "place_b"),
                                             symmetrical=False, related_name="places_related", related_query_name="place_related")

    def __str__(self):
        return self.person_id + "_" + self.place_id


class relationType(models.Model):
    """Describes a relation type in the database."""
    code = models.CharField(max_length=10, blank=True)
    subtype_code = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=50, blank=True)
    name_inverted = models.CharField(max_length=50, blank=True)
    descr = models.CharField(max_length=255, blank=True)
    # # the following makes hierarchical structure of relation types possible (unnecessary complication):
    # parent_types = models.ManyToManyField("self", symmetrical=False, blank=True,
    #                                       related_name="sub_types", related_query_name="sub_type")
    # define the entities between which this relation type exists: person_person, place_place, person_place, ...
    entities = models.CharField(max_length=50, blank=True)

    def __str__(self):
        if self.subtype_code:
            return self.code + "." + self.subtype_code
        else:
            return self.code


class a2bRelation (models.Model):
    """A general model for relations between entities.

    For text to text relations (A is a commentary on B): fill in text_a and text_b
    For person to person relations (A is a student of B): fill in person_a and person_b
    For person to place relations (A was born in B): fill in person_a and place_b
    for text to person relations (A is a biography of B): fill in text_a and person_b

    """
    # define A and B (pick two, depending on the type of relationship):
    person_a = models.ForeignKey(authorMeta, related_name="related_persons_a", related_query_name="related_person_a",
                                    on_delete=models.DO_NOTHING, null=True, blank=True)
    person_b = models.ForeignKey(authorMeta, related_name="related_persons_b", related_query_name="related_person_b",
                                    on_delete=models.DO_NOTHING, null=True, blank=True)
    text_a = models.ForeignKey(textMeta, related_name="related_texts_a", related_query_name="related_text_a",
                                  on_delete=models.DO_NOTHING, null=True, blank=True)
    text_b = models.ForeignKey(textMeta, related_name="related_texts_b", related_query_name="related_text_b",
                                  on_delete=models.DO_NOTHING, null=True, blank=True)
    place_a = models.ForeignKey(placeMeta, related_name="related_places_a", related_query_name="related_place_a",
                                   on_delete=models.DO_NOTHING, null=True, blank=True)
    place_b = models.ForeignKey(placeMeta, related_name="related_places_b", related_query_name="related_place_b",
                                   on_delete=models.DO_NOTHING, null=True, blank=True)

    # define the type of relationship between entity A and entity B:
    relation_type = models.ForeignKey(relationType, on_delete=models.DO_NOTHING, null=True, blank=True)

    # additional information about the relationship (data types need to change!):
    start_date_AH = models.CharField(max_length=100, null=False, blank=True)
    end_date_AH = models.CharField(max_length=100, null=False, blank=True)
    authority = models.CharField(max_length=100, null=False, blank=True)
    confidence = models.IntegerField(null=True, blank=True)

    def __str__(self):
        a = [x for x in [self.person_a, self.text_a, self.place_a] if x]
        b = [x for x in [self.person_b, self.text_b, self.place_b] if x]
        #return str(a[0]) + self.relation_type.name + str(b[0])
        return f"{a[0]} {self.relation_type.name} {b[0]}"

class TextReuseStats(models.Model):
    id = models.AutoField(primary_key=True)
    # book_1 = models.CharField(max_length=50, null=False)
    # book_2 = models.CharField(max_length=50, null=False)
    instances_count = models.IntegerField(null=True, blank=True)
    book1_word_match = models.IntegerField(null=True, blank=True)
    book2_word_match = models.IntegerField(null=True, blank=True)
    book1_match_book2_per = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    book2_match_book1_per = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    book_1 = models.ForeignKey(versionMeta, to_field='version_id', on_delete=models.DO_NOTHING,
                               related_name='textreuse_b1', related_query_name="textreuse_b1")
    book_2 = models.ForeignKey(versionMeta, to_field='version_id', on_delete=models.DO_NOTHING, 
                               related_name='textreuse_b2', related_query_name="textreuse_b2")
    tsv_url = models.CharField(max_length=100, null=False, blank=True)
    release = models.ForeignKey("ReleaseDetails", related_name="reuse_statistics", 
                                related_query_name="reuse_statistics", on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return f"{self.release}_{self.book_1}_{self.book_2}"


class CorpusInsights(models.Model):
    """Describes general statistics on the corpus in a specific release"""
    id = models.AutoField(primary_key=True)
    number_of_unique_authors = models.IntegerField(null=True, blank=True)
    number_of_books = models.IntegerField(null=True, blank=True)
    number_of_versions = models.IntegerField(null=True, blank=True)
    total_word_count = models.IntegerField(null=True, blank=True)
    largest_book = models.IntegerField(null=True, blank=True)
    total_word_count_pri = models.IntegerField(null=True, blank=True)
    top_10_book_by_word_count = models.JSONField(null=True, blank=True)
    release = models.ForeignKey("ReleaseDetails", related_name="corpus_statistics", 
                                related_query_name="corpus_statistics", on_delete=models.DO_NOTHING)

class ReleaseMeta(models.Model):
    """Describes metadata of a digital text version in a specific OpenITI release"""
    id = models.AutoField(primary_key=True)
    #release_code = models.CharField(max_length=10, null=False) # e.g., 2021.2.5
    release = models.ForeignKey("ReleaseDetails", blank=False, on_delete=models.DO_NOTHING) # e.g., 2021.2.5
    version_meta = models.ForeignKey(versionMeta, related_name='releases', related_query_name="release", on_delete=models.DO_NOTHING)
    char_length = models.IntegerField(null=True, blank=True)
    tok_length = models.IntegerField(null=True, blank=True)
    url = models.CharField(max_length=255, null=False, blank=True)
    analysis_priority = models.CharField(max_length=3, null=False, blank=True)  # previous called status option could be pri, sec, tr
    annotation_status = models.CharField(max_length=50, null=False, blank=True) # mARkdown, completed, ...
    notes = models.TextField(null=False, blank=True)

class ReleaseDetails(models.Model):
    """Describes an OpenITI release"""
    id = models.AutoField(primary_key=True)
    release_code = models.CharField(max_length=10, null=False)
    release_date = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
    zenodo_link = models.CharField(max_length=200, null=False, blank=True)
    release_notes = models.TextField(null=False, blank=True)

    def __str__(self):
        return self.release_code


class SourceCollectionDetails(models.Model):
    """Describes the source collection from where texts entered into the OpenITI corpus"""
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=10, unique=True)  #Shamela, Shia,  JK, ...
    url = models.CharField(max_length=200, null=False, blank=True)
    name = models.CharField(max_length=200, null=False)
    description = models.TextField(null=False, blank=True)