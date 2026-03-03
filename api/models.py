# TO DO: add a tags model!

from django.db import models
from django.db.models import Q, Case, When, Value, IntegerField, ExpressionWrapper
import datetime
import convertdate

###############################
# MANY TO MANY HELPERS: NAMES #
###############################

class ObjectName(models.Model):
    """
    Combination of name, language and name_type, 
    useful for enabling multiple names for the same object
    (e.g., shuhra in Arabic, nisba in English, official name in French)
    """
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255)
    # Language tag (3 characters): 
    language = models.CharField(max_length=3, blank=True, db_index=True)

    # optional name type
    name_type = models.CharField(max_length=50, blank=True,
        help_text="e.g. 'shuhra', 'nisba', 'official', 'variant', 'short'")

    class Meta:
        indexes = [
            models.Index(fields=["language", "name"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.language or 'und'}: {self.name}"

class ObjectNameLink(models.Model):
    """
    Single link table: links objects with names, languages and name_types.
    
    If you create a new model that should allow multiple names,
    add a key here and add it to the uniqueness constraints.
    """
    object_name = models.ForeignKey(ObjectName, on_delete=models.CASCADE, 
                                    related_name="links")

    # exactly ONE of these must be set
    author = models.ForeignKey(
        "Author", on_delete=models.CASCADE, null=True, blank=True,
        related_name="object_name_links"
    )
    text = models.ForeignKey(
        "Text", on_delete=models.CASCADE, null=True, blank=True,
        related_name="object_name_links"
    )
    manuscript_holding = models.ForeignKey(
        "ManuscriptHolding", on_delete=models.CASCADE, null=True, blank=True,
        related_name="object_name_links"
    )
    manuscript = models.ForeignKey(
        "Manuscript", on_delete=models.CASCADE, null=True, blank=True,
        related_name="object_name_links"
    )
    place = models.ForeignKey(
        "Place", on_delete=models.CASCADE, null=True, blank=True,
        related_name="object_name_links"
    )

    is_preferred = models.BooleanField(default=False,
        help_text="Is this the preferred name of the object?")
    source = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["author"]),
            models.Index(fields=["text"]),
            models.Index(fields=["place"]),
            models.Index(fields=["manuscript_holding"]),
            models.Index(fields=["manuscript"]),
        ]
        # BUILDUP: UNCOMMENT:
        # constraints = [
        #     # Enforce exactly one FK is non-null
        #     models.CheckConstraint(
        #         name="exactly_one_target_object",
        #         condition=(
        #             (Q(author__isnull=False) & Q(text__isnull=True) & Q(manuscript__isnull=True) & Q(manuscript_holding__isnull=True) & Q(country__isnull=True) & Q(place__isnull=True))
        #             | (Q(author__isnull=True) & Q(text__isnull=False) & Q(manuscript__isnull=True) & Q(manuscript_holding__isnull=True) & Q(country__isnull=True) & Q(place__isnull=True))
        #             | (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript__isnull=False) & Q(manuscript_holding__isnull=True) & Q(country__isnull=True) & Q(place__isnull=True))
        #             | (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript__isnull=True) & Q(manuscript_holding__isnull=False) & Q(country__isnull=True) & Q(place__isnull=True))
        #             | (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript__isnull=True) & Q(manuscript_holding__isnull=True) & Q(country__isnull=False) & Q(place__isnull=True))
        #             | (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript__isnull=True) & Q(manuscript_holding__isnull=True) & Q(country__isnull=True) & Q(place__isnull=False))
        #         )
        #     )
        # ]

    def __str__(self):
        # BUILDUP: UNCOMMENT:
        target = self.author or self.text or self.manuscript_holding or self.manuscript or self.place
        return f"{target} ↔ {self.object_name}"

###############################
# MANY TO MANY HELPERS: DATES #
###############################

class Calendar(models.Model):
    slug = models.SlugField(unique=True)  # "gregorian", "hijri", "julian", ...
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class DateType(models.Model):
    slug = models.SlugField(unique=True)  # "birth", "death", ...
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label

class DatePrecision(models.TextChoices):
    DAY = "day", "Day"
    MONTH = "month", "Month"
    YEAR = "year", "Year"
    TEXT = "text", "Text/Unparsed"

class Date(models.Model):
    """Describes a date in any calendar.
    
    Each date is converted to a date range in CE for querying.
    This conversion is done automatically when manually adding
    a date to the database (using the model's save method). 

    IMPORTANT: when bulk uploading, the save method is not
    called and the date range not computed. 
    Pre-calculate the date range for bulk upload instead!
    """
    date_type = models.ForeignKey(DateType, on_delete=models.PROTECT, related_name="dates")
    calendar = models.ForeignKey(Calendar, on_delete=models.PROTECT, related_name="dates")

    # What the source said (keep this even if you parse it)
    date_str = models.CharField(max_length=255, blank=True)

    # Parsed components *in the original calendar* (nullable for unknown/partial)
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    precision = models.CharField(max_length=10, choices=DatePrecision.choices, default=DatePrecision.DAY)

    # Normalized CE/Gregorian range for querying/sorting
    ce_start = models.DateField(null=True, blank=True, db_index=True)
    ce_end = models.DateField(null=True, blank=True, db_index=True)

    # optional:
    source = models.CharField(max_length=255, blank=True)
    confidence = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.date_type.slug}: {self.date_str or self.iso_like}"

    @property
    def iso_like(self):
        # helpful for display when date_str not provided
        if self.year is None:
            return ""
        if self.precision == DatePrecision.YEAR:
            return f"{self.year:04d}"
        if self.precision == DatePrecision.MONTH and self.month:
            return f"{self.year:04d}-{self.month:02d}"
        if self.month and self.day:
            return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        return f"{self.year:04d}"

    def compute_ce_range(self):
        """
        Compute ce_start/ce_end from (calendar, year, month, day, precision).
        Implement calendar conversions here.
        """
        if self.calendar.slug == "gregorian":
            return self._compute_ce_range_from_gregorian()
        else:
            return self._compute_ce_range_from_other_calendar()

    def _compute_ce_range_from_gregorian(self):
        if self.year is None:
            return (None, None)

        if self.precision == DatePrecision.YEAR:
            start = datetime.date(self.year, 1, 1)
            end = datetime.date(self.year, 12, 31)
            return (start, end)

        if self.precision == DatePrecision.MONTH and self.month:
            start = datetime.date(self.year, self.month, 1)
            # last day of month
            if self.month == 12:
                end = datetime.date(self.year, 12, 31)
            else:
                end = datetime.date(self.year, self.month + 1, 1) - datetime.timedelta(days=1)
            return (start, end)

        if self.month and self.day:
            d = datetime.date(self.year, self.month, self.day)
            return (d, d)

        return (None, None)

    def _compute_ce_range_from_other_calendar(self):
        """
        Compute the CE range from hijri qamari, hijri shamsi, persian, coptic, armenian and hebrew calendar.
        """
        if self.year is None:
            print("NO YEAR GIVEN!", self.year)
            return (None, None)
        
        converters = {
            "AH": convertdate.islamic,
            "hijri": convertdate.islamic,
            "qamari": convertdate.islamic,
            "shamsi": convertdate.persian,
            "persian": convertdate.persian,
            "coptic": convertdate.coptic,
            "armenian": convertdate.armenian,
            "hebrew": convertdate.hebrew
        }
        date_converter = converters.get(self.calendar.slug, None)
        if date_converter is None:
            print("UNKNOWN CALENDAR:", self.calendar.slug)
            return (None, None)
        
        # define the precision if it is not given:
        if self.precision in (DatePrecision.YEAR, DatePrecision.MONTH, DatePrecision.DAY):
            precision = self.precision
        elif not self.month:  # year is defined anyway, otherwise we had already returned (None, None)
            precision = DatePrecision.YEAR
        elif not self.day:
            precision = DatePrecision.MONTH
        else:
            precision = DatePrecision.DAY
        print(precision)
        
        # calculate the date range given the precision
        if precision == DatePrecision.YEAR:
            start = date_converter.to_gregorian(self.year, 1, 1)
            # calculate the last day of the last month in the given year (29 or 30 days!):
            last_day = date_converter.month_length(self.year, 12)
            end = date_converter.to_gregorian(self.year, 12, last_day)
            return (self.to_datetime(start), self.to_datetime(end))

        if precision == DatePrecision.MONTH and self.month:
            start = date_converter.to_gregorian(self.year, self.month, 1)
            # last day of month
            last_day = date_converter.month_length(self.year, self.month)
            end = date_converter.to_gregorian(self.year, self.month, last_day)
            return (self.to_datetime(start), self.to_datetime(end))

        if self.month and self.day:
            d = date_converter.to_gregorian(self.year, self.month, self.day)
            d = self.to_datetime(d)
            return (d, d)

        return (None, None)

    def to_datetime(self, gregorian_tuple):
        """
        convertdate.<cal>.to_gregorian returns (year, month, day) tuples.
        Convert to datetime.date.
        """
        if not gregorian_tuple:
            return None
        y, m, d = gregorian_tuple
        return datetime.date(int(y), int(m), int(d))

    def save(self, *args, **kwargs):
        """This will automatically convert the CE ranges if a date is manually added.
        However, this does not work with bulk_upload because that doesn't call the save function!
        Pre-calculate the CE ranges for bulk upload instead."""
        if self.ce_start is not None and self.ce_end is not None:
            return super().save(*args, **kwargs)
        print("RECALCULATING CE_START AND CE_END")
        if self.precision != DatePrecision.TEXT:
            self.ce_start, self.ce_end = self.compute_ce_range()
        else:
            self.ce_start, self.ce_end = (None, None)
        super().save(*args, **kwargs)

class DateLink(models.Model):
    """
    Single link table: Links an author, text or edition object to a date.
    If you want to add dates to another model, make sure to add a foreignkey
    to that model here, and to include it in the constraints
    """
    date = models.ForeignKey("Date", on_delete=models.CASCADE, related_name="links")

    author = models.ForeignKey("Author", on_delete=models.CASCADE, null=True, blank=True, 
                               related_name="date_links")
    text = models.ForeignKey("Text", on_delete=models.CASCADE, null=True, blank=True, 
                             related_name="date_links")
    edition = models.ForeignKey("Edition", on_delete=models.CASCADE, null=True, blank=True, 
                               related_name="date_links")
    manuscript = models.ForeignKey("Manuscript", on_delete=models.CASCADE, null=True, blank=True, 
                               related_name="date_links")

    # Optional relationship metadata: 
    is_preferred = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["author"]),
            models.Index(fields=["text"]),
            models.Index(fields=["edition"]),
            models.Index(fields=["manuscript"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="date_exactly_one_target_author_text_edition",
                condition=( 
                    Q(author__isnull=False)
                    # BUILDUP: UNCOMMENT:
                    # (Q(author__isnull=False) & Q(text__isnull=True) & Q(edition__isnull=True) & Q(manuscript__isnull=True))
                    # | (Q(author__isnull=True) & Q(text__isnull=False) & Q(edition__isnull=True) & Q(manuscript__isnull=True))
                    # | (Q(author__isnull=True) & Q(text__isnull=True) & Q(edition__isnull=False) & Q(manuscript__isnull=True))
                    # | (Q(author__isnull=True) & Q(text__isnull=True) & Q(edition__isnull=True) & Q(manuscript__isnull=False))

                ),
            )
        ]

    def __str__(self):
        # BUILDUP: UNCOMMENT:
        target = self.author or self.text or self.edition or self.manuscript
        return f"{target} ↔ {self.date}"

##############################################
# MANY TO MANY HELPERS: EXTERNAL IDENTIFIERS #
##############################################

class IdentifierProvider(models.Model):
    """
    The namespace/provider for authority control: VIAF, Wikidata, GeoNames, ISNI, ...
    """
    slug = models.SlugField(unique=True)   # e.g. "viaf", "wikidata", "geonames"
    name = models.CharField(max_length=100)
    # optionally, provide the base link that, combined with the ID,
    # gives you a direct link to the object: e.g. https://www.wikidata.org/wiki/
    base_url = models.URLField(blank=True) 

    def __str__(self):
        return self.name

class ExternalID(models.Model):
    """External identifier (e.g. Wikidata QID, VIAF id, GeoNames id)"""
    provider = models.ForeignKey(IdentifierProvider,on_delete=models.PROTECT,related_name="external_ids")
    external_id = models.CharField(max_length=255)

    @property
    def url(self):
        """Generate the direct link to the object if a base_url is provided"""
        if self.provider.base_url:
            return f"{self.provider.base_url}{self.external_id}"
        return ""

    class Meta:
        indexes = [
            models.Index(fields=["provider", "external_id"]),
            models.Index(fields=["external_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"],
                name="uniq_provider_external_id",
            )
        ]

    def __str__(self):
        return f"{self.provider.slug}:{self.external_id}"

class ExternalIDLink(models.Model):
    """
    Single link table: links an ExternalID to exactly one of
    (Author, Text, ManuscriptHolding, Place, Edition, Version, Country).
    """
    identifier = models.ForeignKey("ExternalID", on_delete=models.CASCADE, related_name="links")

    # Exactly ONE of these must be set:
    author = models.ForeignKey("Author", on_delete=models.CASCADE, 
                               null=True, blank=True, related_name="external_id_links")
    text = models.ForeignKey("Text", on_delete=models.CASCADE, 
                             null=True, blank=True, related_name="external_id_links")
    manuscript_holding = models.ForeignKey("ManuscriptHolding", on_delete=models.CASCADE, 
                                           null=True, blank=True, related_name="external_id_links")
    manuscript = models.ForeignKey("Manuscript", on_delete=models.CASCADE,
                                 null=True, blank=True, related_name="external_id_links")
    place = models.ForeignKey("Place", on_delete=models.CASCADE, 
                              null=True, blank=True, related_name="external_id_links")
    edition = models.ForeignKey("Edition", on_delete=models.CASCADE, 
                                null=True, blank=True, related_name="external_id_links")
    version = models.ForeignKey("Version", on_delete=models.CASCADE, 
                                null=True, blank=True, related_name="external_id_links")
    

    #is_preferred = models.BooleanField(default=False)
    #source = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["identifier"]),
            models.Index(fields=["author"]),
            models.Index(fields=["text"]),
            models.Index(fields=["manuscript_holding"]),
            models.Index(fields=["place"]),
            models.Index(fields=["edition"]),
            models.Index(fields=["version"]),
            models.Index(fields=["manuscript"]),
        ]
        constraints = [
            # Enforce exactly one target object
            models.CheckConstraint(
                name="externalid_exactly_one_target",
                # condition=ExpressionWrapper(
                #     (
                #         Case(When(author__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                #         Case(When(text__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                #         Case(When(version__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                #         Case(When(edition__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                #         Case(When(manuscript_holding__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                #         Case(When(place__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                #         Case(When(manuscript__isnull=False, then=Value(1)), default=Value(0), output_field=IntegerField())
                #     ) == Value(1),
                #     output_field=models.BooleanField()
                # )
                condition=(
                    # author only
                    (Q(author__isnull=False) & Q(text__isnull=True) & Q(manuscript_holding__isnull=True) & Q(place__isnull=True)
                     & Q(edition__isnull=True) & Q(version__isnull=True) & Q(manuscript__isnull=True))
                    |
                    # text only
                    (Q(author__isnull=True) & Q(text__isnull=False) & Q(manuscript_holding__isnull=True) & Q(place__isnull=True)
                     & Q(edition__isnull=True) & Q(version__isnull=True) & Q(manuscript__isnull=True))
                    |
                    # manuscript_holding only
                    (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript_holding__isnull=False) & Q(place__isnull=True)
                     & Q(edition__isnull=True) & Q(version__isnull=True) & Q(manuscript__isnull=True))
                    |
                    # place only
                    (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript_holding__isnull=True) & Q(place__isnull=False)
                     & Q(edition__isnull=True) & Q(version__isnull=True) & Q(manuscript__isnull=True))
                    |
                    # edition only
                    (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript_holding__isnull=True) & Q(place__isnull=True)
                     & Q(edition__isnull=False) & Q(version__isnull=True) & Q(manuscript__isnull=True))
                    |
                    # version only
                    (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript_holding__isnull=True) & Q(place__isnull=True)
                     & Q(edition__isnull=True) & Q(version__isnull=False) & Q(manuscript__isnull=True))
                    |
                    # country only
                    (Q(author__isnull=True) & Q(text__isnull=True) & Q(manuscript_holding__isnull=True) & Q(place__isnull=True)
                     & Q(edition__isnull=True) & Q(version__isnull=True) & Q(manuscript__isnull=False))
                ),
            ),
        ]

    def __str__(self):
        target = (
            self.author or self.text or self.manuscript_holding or
            self.place or self.edition or self.version or self.country
        )
        return f"{target} <-> {self.identifier}"

##################################
# MANY TO MANY HELPERS: TEXTTYPE #
##################################

class TextType(models.Model):
    """
    Controlled vocabulary for classifying texts/manuscripts
    (e.g. poetry, commentary, legal, biography, etc.)
    """
    slug = models.SlugField(unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.label


class TextTypeLink(models.Model):
    text_type = models.ForeignKey(TextType, on_delete=models.CASCADE, related_name="links")

    # Exactly ONE must be set
    text = models.ForeignKey("Text", on_delete=models.CASCADE, 
        null=True, blank=True, related_name="text_type_links")

    manuscript = models.ForeignKey("Manuscript", on_delete=models.CASCADE, 
        null=True, blank=True, related_name="text_type_links")

    # Optional metadata
    is_preferred = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["text_type"]),
            models.Index(fields=["text"]),
            models.Index(fields=["manuscript"]),
        ]
        constraints = [
            # Enforce exactly one target object
            models.CheckConstraint(
                name="texttype_exactly_one_target",
                condition=( 
                    (Q(text__isnull=False) & Q(manuscript__isnull=True))
                    | (Q(text__isnull=True) & Q(manuscript__isnull=False))
                ),
            )
        ]

    def __str__(self):
        # BUILDUP: UNCOMMENT:
        target = self.text or self.manuscript
        return f"{target} <-> {self.text_type}"

####################################
# MANY TO MANY HELPERS: AUTHORSHIP #
####################################

# class AuthorshipRole(models.Model):
#     slug = models.SlugField(unique=True)   # "author", "translator", "commentator"
#     label = models.CharField(max_length=100)
#     description = models.TextField(blank=True)

#     def __str__(self):
#         return self.label


# class AuthorshipRoleLink(models.Model):
#     author = models.ForeignKey("Author", on_delete=models.CASCADE, related_name="text_links")
#     role = models.ForeignKey("TextType", on_delete=models.CASCADE, related_name="links")

#     # Exactly ONE must be set
#     text = models.ForeignKey("Text", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="author_links")

#     manuscript = models.ForeignKey("Manuscript", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="author_links")
    
#     edition = models.ForeignKey("Edition", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="author_links")

#     # Optional metadata
#     note = models.CharField(max_length=255, blank=True)

#     class Meta:
#         indexes = [
#             models.Index(fields=["author"]),
#             models.Index(fields=["role"]),
#             models.Index(fields=["text"]),
#             models.Index(fields=["edition"]),
#             models.Index(fields=["manuscript"]),
#         ]
#         constraints = [
#             # Enforce exactly one target object
#             models.CheckConstraint(
#                 name="authorship_exactly_one_target",
#                 condition=(  
#                     (Q(text__isnull=False) & Q(edition__isnull=True) & Q(manuscript__isnull=True))
#                     | (Q(text__isnull=True) & Q(edition__isnull=False) & Q(manuscript__isnull=True))
#                     | (Q(text__isnull=True) & Q(edition__isnull=True) & Q(manuscript__isnull=False))
#                 ),
#             )
#         ]

#     def __str__(self):
#         target = self.text or self.edition or self.manuscript
#         return f"{self.author} - {self.role} - {target}"
    


################################
# MANY TO MANY HELPERS: PLACES #
################################


# class PlaceRelationType(models.Model):
#     """
#     Controlled vocabulary for how something relates to a place.
#     Examples:
#       - Person: born_in, died_in, resided_in
#       - Text / Manuscript: written_in, copied_in, composed_in
#       - Edition: published_in, edited_in
#       - ManuscriptHolding: located_in
#     """
#     slug = models.SlugField(unique=True)   # e.g. "born_in", "written_in", "held_in"
#     label = models.CharField(max_length=100)
#     description = models.TextField(blank=True)

#     # Optional: specify which entity types this relation applies to
#     applies_to = models.CharField(
#         max_length=50,
#         blank=True,
#         help_text="Optional hint: 'author', 'text', 'edition', 'manuscript', 'holding' (or leave blank)."
#     )

#     def __str__(self):
#         return self.label


# class PlaceLink(models.Model):
#     """
#     Single link table: links exactly one target object (Author/Text/Edition/ManuscriptHolding/Manuscript)
#     to a Place, with a controlled relation type.
#     """
#     place = models.ForeignKey("Place", on_delete=models.CASCADE, related_name="place_links")
#     relation_type = models.ForeignKey(PlaceRelationType, on_delete=models.PROTECT, related_name="links")

#     # Exactly ONE of these must be set:
#     author = models.ForeignKey("Author", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="place_links")
#     text = models.ForeignKey("Text", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="place_links")
#     edition = models.ForeignKey("Edition", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="place_links")
#     manuscript_holding = models.ForeignKey("ManuscriptHolding", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="place_links")
#     manuscript = models.ForeignKey("Manuscript", on_delete=models.CASCADE, 
#         null=True, blank=True, related_name="place_links")

#     # Optional metadata
#     start_date = models.ForeignKey("Date", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
#     end_date = models.ForeignKey("Date", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
#     note = models.CharField(max_length=255, blank=True)
#     source = models.CharField(max_length=255, blank=True)

#     class Meta:
#         indexes = [
#             models.Index(fields=["place"]),
#             models.Index(fields=["relation_type"]),
#             models.Index(fields=["author"]),
#             models.Index(fields=["text"]),
#             models.Index(fields=["edition"]),
#             models.Index(fields=["manuscript_holding"]),
#             models.Index(fields=["manuscript"]),
#         ]
#         constraints = [
#             # Exactly one target object
#             models.CheckConstraint(
#                 name="placelink_exactly_one_target",
#                 condition=(  
#                     (Q(author__isnull=False) & Q(text__isnull=True) & Q(edition__isnull=True) & Q(manuscript_holding__isnull=True) & Q(manuscript__isnull=True))
#                     | (Q(author__isnull=True) & Q(text__isnull=False) & Q(edition__isnull=True) & Q(manuscript_holding__isnull=True) & Q(manuscript__isnull=True))
#                     | (Q(author__isnull=True) & Q(text__isnull=True) & Q(edition__isnull=False) & Q(manuscript_holding__isnull=True) & Q(manuscript__isnull=True))
#                     | (Q(author__isnull=True) & Q(text__isnull=True) & Q(edition__isnull=True) & Q(manuscript_holding__isnull=False) & Q(manuscript__isnull=True))
#                     | (Q(author__isnull=True) & Q(text__isnull=True) & Q(edition__isnull=True) & Q(manuscript_holding__isnull=True) & Q(manuscript__isnull=False))
#                 ),
#             ),
#         ]

#     def __str__(self):
#         target = self.author or self.text or self.edition or self.manuscript_holding or self.manuscript
#         return f"{target} — {self.relation_type.slug} — {self.place}"

###############
# MAIN MODELS #
###############

class Author(models.Model):
    """Describes a person in the database."""
    author_uri = models.CharField(max_length=50, null=False)

    # names of different types (shuhra, nisba, ...) and in different languages/scripts: 
    names =  models.ManyToManyField(ObjectName, through=ObjectNameLink,
        through_fields=("author", "object_name"), related_name="authors", blank=True
    )
   
    # multiple types of dates (birth, death, ...) for the author, in different calendars:
    dates = models.ManyToManyField(Date, through=DateLink,
        through_fields=("author", "date"), related_name="authors", blank=True
    )

    tags =  models.CharField(max_length=255, blank=True)
    bibliography = models.TextField(null=False, blank=True)
    notes = models.TextField(null=False, blank=True)

    external_ids = models.ManyToManyField(ExternalID, through=ExternalIDLink,
                    through_fields=("author", "identifier"),  
                    related_name="authors", blank=True)

    # Create a relationship between two persons (e.g., person A is a student of person B)
    # using a many-to-many field:
    related_persons = models.ManyToManyField(
        "self",  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        through="A2BRelation", # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through
        through_fields=("person_a", "person_b"), # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.through_fields
        symmetrical=False,  # see https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField.symmetrical
        related_name="persons_related",
        related_query_name="person_related"
    )
    # Create a relationship between a person and a place (e.g., person A was born in place B)
    # using a many-to-many field:
    related_places = models.ManyToManyField("Place", through="A2BRelation", through_fields=("person_a", "place_b"), 
                                            related_name="related_persons", related_query_name="related_person")
    # NB: person to text relations are defined in the Text model

    def __str__(self):
        return self.author_uri

class Text(models.Model):
    """Describes a text in the database."""
    text_uri = models.CharField(max_length=100, unique=True, null=False)
    
    # multiple authors (with different roles):
    authors = models.ManyToManyField("Author", 
        through="A2BRelation",
        through_fields=("text_b", "person_a"), 
        related_name="texts", blank=True
    )
    # old key:
    #author = models.ForeignKey(Author, on_delete=models.DO_NOTHING,
    #                               related_name='texts', related_query_name="text")

    # multiple titles for the text, in multiple languages:
    titles = models.ManyToManyField(ObjectName, blank=True, 
        through=ObjectNameLink,
        through_fields=("text", "object_name"), 
        related_name="texts"
    )
    # old keys:
    #titles_ar = models.CharField(max_length=255, blank=True)
    #titles_lat = models.CharField(max_length=255, blank=True)
    #title_ar_prefered = models.CharField(max_length=255, blank=True)
    #title_lat_prefered = models.CharField(max_length=255, blank=True)

    # multiple types of dates (written, ...) for the text, in different calendars:
    dates = models.ManyToManyField(Date, blank=True, 
        through=DateLink,
        through_fields=("text", "date"), 
        related_name="texts"
    )
    
    #text_type = models.CharField(max_length=15, blank=True)  # document, inscription, ...
    text_types = models.ManyToManyField(TextType, blank=True, 
        through=TextTypeLink,
        through_fields=("text", "text_type"), 
        related_name="texts"
    )
    tags =  models.CharField(max_length=255, blank=True)
    bibliography = models.TextField(null=False, blank=True)
    notes = models.TextField(null=False, blank=True)
    external_ids = models.ManyToManyField(ExternalID, through=ExternalIDLink,
        through_fields=("text", "identifier"),  
        related_name="texts", blank=True
    )

    # Create a relationship between two texts (e.g., text A is a commentary on text B)
    # using a many-to-many field:
    related_texts = models.ManyToManyField("self", 
        through="A2BRelation", 
        through_fields=("text_a", "text_b"),
        symmetrical=False, 
        related_name="texts_related", 
        related_query_name="text_related")
    # Create a relationship between a text and a person (e.g., text A is a biography of person B)
    # using a many-to-many field:
    related_persons = models.ManyToManyField("Author", 
        through="A2BRelation", 
        through_fields=("text_a", "person_b"),
        related_name="related_texts", 
        related_query_name="related_text")
    # Create a relationship between a text and a place (e.g., text A is a history of place B; text A was written in place B)
    # using a many-to-many field:
    related_places = models.ManyToManyField("Place", through="A2BRelation", through_fields=("text_a", "place_b"),
                                            related_name="related_texts", related_query_name="related_text")

    def __str__(self):
        return self.text_uri

class Script(models.Model):
    code = models.CharField(max_length=50, 
        blank=False, null=False)
    name = models.CharField(max_length=100, 
        blank=True, null=False)
    description = models.TextField(
        blank=True, null=False)

class Language(models.Model):
    code = models.CharField(max_length=50, 
        blank=False, null=False)
    name = models.CharField(max_length=100, 
        blank=True, null=False)
    description = models.TextField(
        blank=True, null=False)
    
class SubCorpus(models.Model):
    code = models.CharField(max_length=10, 
        blank=False, null=False)
    name = models.CharField(max_length=100, 
        blank=True, null=False)
    description = models.TextField(
        blank=True, null=False)

class LanguageScriptCombo(models.Model):
    """Describes the combination of language and 
    the script used to write it.

    Some languages are written in multiple scripts, 
    e.g., Persian is usually written in Arabic script, 
    but Judaeo-Persian is Persian in Hebrew script.
    """
    code = models.CharField(max_length=3, 
        blank=False, null=False)
    name = models.CharField(max_length=50, 
        blank=True, null=False)
    description = models.TextField(
        blank=True, null=False)
    language = models.ForeignKey("Language", blank=True, null=True,
        related_name="language_script_combo", 
        on_delete=models.DO_NOTHING)
    script = models.ForeignKey("Script", blank=True, null=True,
        related_name="language_script_combo", 
        on_delete=models.DO_NOTHING)

class Version(models.Model):
    """Describes a digital version of a text in the database.
    
    Only metadata of the version that cannot change
    (or, if it is changed, should be overwritten: e.g., typos)
    are stored in this model; store metadata that can change
    across versions (e.g., notes, char_lenght, tok length, url, 
    status and annotation status) in ReleaseVersion.
    """
    version_code = models.CharField(max_length=50, null=False)
    version_uri = models.CharField(max_length=100, unique=True, blank=True)
    text = models.ForeignKey(Text, blank=True, null=True,
        related_name='versions', related_query_name="version", 
        on_delete=models.DO_NOTHING)
    manuscript = models.ForeignKey("Manuscript", blank=True, null=True,
        related_name='transcriptions', related_query_name="transcription", 
        on_delete=models.DO_NOTHING)
    language = models.CharField(max_length=25, blank=True)
    language_script_combo = models.ManyToManyField(LanguageScriptCombo,
        related_name='versions', related_query_name="version",
        blank=True) 
    edition = models.ForeignKey("Edition", blank=True, null=True,
        related_name='versions', related_query_name="version", 
        on_delete=models.DO_NOTHING)
    source_coll = models.ForeignKey("SourceCollectionDetails", 
        related_name='versions', related_query_name="version", 
        on_delete=models.DO_NOTHING, blank=True, null=True)
    part_of = models.ForeignKey("self", related_name='parts', related_query_name="part", 
                                on_delete=models.DO_NOTHING, blank=True, null=True)
    external_ids = models.ManyToManyField(ExternalID, through=ExternalIDLink,
                    through_fields=("version", "identifier"),  
                    related_name="versions", blank=True)


    def __str__(self):
        return self.version_uri


class Edition(models.Model):
    editor = models.CharField(max_length=100, blank=True)
    edition_place = models.CharField(max_length=100, blank=True)
    # ALTERNATIVELY:
    # edition_place = models.ManyToManyField("Place", through="A2BRelation", through_fields=("edition_a", "edition_b"),
    #                                         related_name="editions", related_query_name="edition")
    publisher = models.CharField(max_length=100, blank=True)
    #edition_date = models.CharField(max_length=100, blank=True)
    # multiple types of dates (edition, translation, ...) for the edition, in different calendars:
    dates = models.ManyToManyField(Date, through=DateLink,
        through_fields=("edition", "date"), related_name="editions", blank=True
    )
    ed_info = models.CharField(max_length=255, blank=True)
    pdf_url = models.CharField(max_length=255, blank=True)
    text = models.ForeignKey(Text, 
        related_name='editions',
        related_query_name="edition", on_delete=models.CASCADE)
    # manuscript = models.ForeignKey("Manuscript",  blank=True, null=True,
    #     related_name='editions',
    #     related_query_name="edition", on_delete=models.CASCADE)
    
    external_ids = models.ManyToManyField(ExternalID, through=ExternalIDLink,
                    through_fields=("edition", "identifier"),  
                    related_name="editions", blank=True)
    
    def __str__(self):
        return self.ed_info

class ManuscriptHolding(models.Model):
    """Describes a manuscript holding  (institution, private collection) in the database."""
    loc_uri = models.CharField(max_length=50, null=False)
    names = models.ManyToManyField(ObjectName, through=ObjectNameLink,
        through_fields=("manuscript_holding", "object_name"), 
        related_name="manuscript_holdings", blank=True
    )
    country = models.ForeignKey("Place", related_name="country_manuscript_holdings", 
                                on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey("Place", related_name="city_manuscript_holdings", 
                             on_delete=models.CASCADE, null=True, blank=True)
    external_ids = models.ManyToManyField(ExternalID, through=ExternalIDLink,
                    through_fields=("manuscript_holding", "identifier"),
                    related_name="manuscript_holdings", blank=True)
    notes = models.TextField(null=False, blank=True)

    def __str__(self):
        return self.loc_uri


class Manuscript(models.Model):
    """Describes a manuscript in the database."""
    manuscript_holding = models.ForeignKey(ManuscriptHolding,
        related_name="manuscripts", related_query_name="manuscript",
        on_delete=models.DO_NOTHING)
    manuscript_uri = models.CharField(max_length=100, null=False)
    shelfmark = models.CharField(max_length=255, blank=True)
    catalog_reference = models.CharField(max_length=255, blank=True)
    script = models.CharField(max_length=255, blank=True)
    binding = models.CharField(max_length=255, blank=True)
    colophon = models.TextField(blank=True)
    incipit = models.TextField(blank=True)
    explicit = models.TextField(blank=True)
    columns = models.IntegerField(null=True, default=None)
    decoration = models.TextField(blank=True)
    hands = models.TextField(blank=True)
    height = models.FloatField(null=True, default=None)
    width = models.FloatField(null=True, default=None)
    ink = models.CharField(max_length=255, blank=True)
    lines_per_page = models.CharField(max_length=255, blank=True)
    stamps = models.TextField(blank=True)
    volumes = models.CharField(max_length=100, blank=True)
    external_ids = models.ManyToManyField(ExternalID,                                   
        through=ExternalIDLink,
        through_fields=("manuscript", "identifier"),  
        related_name="manuscripts", blank=True)
    manuscript_types = models.ManyToManyField(TextType, 
        through=TextTypeLink,
        through_fields=("manuscript", "text_type"), 
        related_name="manuscripts", blank=True
    )
    related_persons = models.ManyToManyField("Author", through="A2BRelation",
        through_fields=("manuscript_b", "person_a"), related_name="manuscripts", blank=True
    )
    titles = models.ManyToManyField(ObjectName, through=ObjectNameLink,
        through_fields=("manuscript", "object_name"), related_name="manuscripts", blank=True
    )
    related_texts = models.ManyToManyField("Text", through="A2BRelation",
        through_fields=("manuscript_a", "text_b"), related_name="manuscripts", blank=True
    )
    related_manuscripts = models.ManyToManyField("self", through="A2BRelation",
        through_fields=("manuscript_a", "manuscript_b"), 
        symmetrical=False, blank=True,
        related_name="manuscripts_related", 
        related_query_name="manuscript_related"
    )
    dates = models.ManyToManyField(Date, through=DateLink,
        through_fields=("manuscript", "date"), related_name="manuscripts", blank=True
    )
    related_places = models.ManyToManyField("Place", through="A2BRelation",
        through_fields=("manuscript_a", "place_b"), related_name="manuscripts", blank=True
    )
    tags =  models.CharField(max_length=255, blank=True)
    bibliography = models.TextField(null=False, blank=True)
    notes = models.TextField(null=False, blank=True)

# BUILDUP: UNCOMMENT:
# class Country(models.Model):
#     """Describes a country/state"""
#     country_code = models.CharField(max_length=4, blank=True)
#     # multilingual names:
#     names =  models.ManyToManyField(ObjectName, through=ObjectNameLink,
#         through_fields=("object_name", "country"), related_name="countries", blank=True
#     )
#     external_ids = models.ManyToManyField(ExternalID, through=ExternalIDLink,
#                     through_fields=("identifier", "country"),  
#                     related_name="countries", blank=True)

#     def __str__(self):
#         return self.country_code

class Place(models.Model):
    """Describes a place in the database."""
    external_ids = models.ManyToManyField(ExternalID, through=ExternalIDLink,
                    through_fields=("place", "identifier"),  
                    related_name="places", blank=True)
    # # old key:
    # #thuraya_uri = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=100, blank=True)
    names =  models.ManyToManyField(ObjectName, through=ObjectNameLink,
        through_fields=("place", "object_name"), related_name="places", blank=True
    )
    # old keys: 
    #name_ar = models.CharField(max_length=100, blank=True)
    #name_lat = models.CharField(max_length=100, blank=True)

    # store coordinates as a string and as decimal fields
    coordinates_str = models.CharField(max_length=50, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Define relation between places (A is capital of B, place A is in region B, region A is in region B, ...):
    related_places = models.ManyToManyField("self", through="A2BRelation", through_fields=("place_a", "place_b"),
                                             symmetrical=False, related_name="places_related", related_query_name="place_related")
    # call code, for countries:
    country_code = models.CharField(max_length=4, blank=True)
    
    def __str__(self):
        first_name = self.names.first()
        return first_name.name if first_name else f"Place {self.pk}"

class RelationType(models.Model):
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


class A2BRelation(models.Model):
    """A general model for relations between entities.

    For text to text relations (A is a commentary on B): fill in text_a and text_b
    For person to person relations (A is a student of B): fill in person_a and person_b
    For person to place relations (A was born in B): fill in person_a and place_b
    For authorship relations (A is the author of B; A is the translator of B): fill in person_a and text_b
    For other text to person relations (A is a biography of B): fill in text_a and person_b
    For manuscript to text relations (A is a witness of B): fill in manuscript_a and text_b
    For person to manuscript relations (A is the copyist of B): fill in person_a and manuscript_b
    
    """
    # define A and B (pick two, depending on the type of relationship):
    person_a = models.ForeignKey(Author, 
        related_name="related_persons_a", related_query_name="related_person_a",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    person_b = models.ForeignKey(Author, 
        related_name="related_persons_b", related_query_name="related_person_b",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    text_a = models.ForeignKey(Text, 
        related_name="related_texts_a", related_query_name="related_text_a",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    text_b = models.ForeignKey(Text, 
        related_name="related_texts_b", related_query_name="related_text_b",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    edition_a = models.ForeignKey(Edition, 
        related_name="related_editions_a", related_query_name="related_edition_a",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    edition_b = models.ForeignKey(Edition, 
        related_name="related_editions_b", related_query_name="related_edition_b",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    place_a = models.ForeignKey(Place, 
        related_name="related_places_a", related_query_name="related_place_a",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    place_b = models.ForeignKey(Place, 
        related_name="related_places_b", related_query_name="related_place_b",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    manuscript_a = models.ForeignKey(Manuscript, 
        related_name="related_manuscripts_a", related_query_name="related_manuscript_a",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    manuscript_b = models.ForeignKey(Manuscript, 
        related_name="related_manuscripts_b", related_query_name="related_manuscript_b",
        on_delete=models.DO_NOTHING, null=True, blank=True)
    

    # define the type of relationship between entity A and entity B:
    relation_type = models.ForeignKey(RelationType, on_delete=models.DO_NOTHING, null=True, blank=True)

    # BUILDUP: UNCOMMENT:
    # # additional information about the relationship (data types need to change!):
    # ## old field names, to be replaced with references to Date fields:
    # ##start_date_AH = models.CharField(max_length=100, null=False, blank=True)
    # ##end_date_AH = models.CharField(max_length=100, null=False, blank=True)
    # start_date = models.ForeignKey("Date", null=True, blank=True, 
    #                                on_delete=models.SET_NULL, related_name="+")
    # end_date = models.ForeignKey("Date", null=True, blank=True, 
    #                              on_delete=models.SET_NULL, related_name="+")
    authority = models.CharField(max_length=100, null=False, blank=True)
    confidence = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        a = [x for x in [self.person_a, self.text_a, self.place_a, self.manuscript_a, self.edition_a] if x]
        b = [x for x in [self.person_b, self.text_b, self.place_b, self.manuscript_b, self.edition_b] if x]
        
        return f"{a[0]} {self.relation_type.name} {b[0]}"

# BUILDUP: UNCOMMENT:
# class TextReuseStats(models.Model):
#     id = models.AutoField(primary_key=True)
#     instances_count = models.IntegerField(null=True, blank=True)
#     book1_words_matched = models.IntegerField(null=True, blank=True)
#     book2_words_matched = models.IntegerField(null=True, blank=True)
#     book1_pct_words_matched = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
#     book2_pct_words_matched = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
#     book_1 = models.ForeignKey("ReleaseVersion", on_delete=models.DO_NOTHING,
#                                related_name='textreuse_b1', related_query_name="textreuse_b1")
#     book_2 = models.ForeignKey("ReleaseVersion", on_delete=models.DO_NOTHING, 
#                                related_name='textreuse_b2', related_query_name="textreuse_b2")
#     tsv_url = models.CharField(max_length=100, null=False, blank=True)
#     release_info = models.ForeignKey("ReleaseInfo", related_name="reuse_statistics", 
#                                 related_query_name="reuse_statistics", on_delete=models.DO_NOTHING)
    
#     def __str__(self):
#         return f"{self.book_1}_{self.book_2}"

# BUILDUP: UNCOMMENT:
# class CorpusInsights(models.Model):
#     """Describes general statistics on the corpus in a specific release"""
#     id = models.AutoField(primary_key=True)
#     number_of_authors = models.IntegerField(null=True, blank=True)
#     number_of_books = models.IntegerField(null=True, blank=True)
#     number_of_versions = models.IntegerField(null=True, blank=True)
#     number_of_pri_versions = models.IntegerField(null=True, blank=True)
#     number_of_sec_versions = models.IntegerField(null=True, blank=True)
#     number_of_markdown_versions = models.IntegerField(null=True, blank=True)
#     number_of_completed_versions = models.IntegerField(null=True, blank=True)
#     total_word_count = models.IntegerField(null=True, blank=True)
#     total_word_count_pri = models.IntegerField(null=True, blank=True)
#     largest_book = models.IntegerField(null=True, blank=True)
#     largest_10_books = models.JSONField(null=True, blank=True)
#     release_info = models.ForeignKey("ReleaseInfo", related_name="corpus_statistics", 
#                                 related_query_name="corpus_statistics", on_delete=models.DO_NOTHING)

#     def __str__(self):
#         return f"{self.release_info} corpus insights"

class ReleaseVersion(models.Model):
    """Describes metadata of a digital text version in a specific OpenITI release"""
    id = models.AutoField(primary_key=True)
    #release_code = models.CharField(max_length=10, null=False) # e.g., 2021.2.5
    release_info = models.ForeignKey("ReleaseInfo", blank=False, on_delete=models.DO_NOTHING) # e.g., 2021.2.5
    version = models.ForeignKey(Version, on_delete=models.DO_NOTHING, 
        related_name='release_versions', 
        related_query_name="release_version")
    char_length = models.IntegerField(null=True, blank=True)
    tok_length = models.IntegerField(null=True, blank=True)
    url = models.CharField(max_length=255, null=False, blank=True)
    subcorpus = models.ForeignKey(SubCorpus, null=True, blank=True,
        related_name="release_versions",
        on_delete=models.DO_NOTHING)
    analysis_priority = models.CharField(max_length=3, null=False, blank=True,
        help_text="Primary or secondary text? Use 'pri' or 'sec'")
    annotation_status = models.CharField(max_length=50, null=False, blank=True,
        help_text="Extension of the file, indicating how far it has been annotated: inProgress, completed, mARkdown")
    line_model = models.CharField(max_length=50, null=False, blank=True,
        help_text="line recognition model used for OCR")
    region_model = models.CharField(max_length=50, null=False, blank=True,
        help_text="region recognition model used for OCR")
    recognition_model = models.CharField(max_length=50, null=False, blank=True,
        help_text="character recognition/transcription model used for OCR")
    contributors = models.ManyToManyField("Contributor", blank=True, 
        related_name='release_versions', related_query_name="release_version")
    uncorrected_ocr = models.BooleanField(default=False,
        help_text="Was this version generated by OCR and not manually corrected?")
    page_range = models.CharField(max_length=50, blank=True, null=False)
    tags = models.CharField(max_length=100, blank=True)
    notes = models.TextField(null=False, blank=True)

    def __str__(self):
        return f"{self.version} ({self.release_info})"
    
class Contributor(models.Model):
    code = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=255, blank=True)
    url = models.CharField(max_length=255, blank=True)
    affiliation = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} ({self.name})"

    
# BUILDUP: UNCOMMENT:
# class VersionwiseReuseStats(models.Model):
#     """Describes text reuse statistics on the single release version level
#     (how many versions does it share text reuse with? How many text reuse instances?)
#     """
#     id = models.AutoField(primary_key=True)
#     release_version = models.ForeignKey(ReleaseVersion, on_delete=models.DO_NOTHING, 
#                                            related_name='versionwise_reuse_stats', 
#                                            related_query_name="versionwise_reuse")
#     n_instances = models.IntegerField(null=True, blank=True)
#     n_versions = models.IntegerField(null=True, blank=True)
#     # TO DO: 
#     #passim_run = models.ForeignKey("PassimRun", blank=False, 
#     #                               related_name='passim_runs', related_query_name="passim_run",
#     #                               on_delete=models.DO_NOTHING)

#     def __str__(self):
#         return f"{self.release_version}: {self.n_instances}, {self.n_versions}"


class ReleaseInfo(models.Model):
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
    affiliation = models.CharField(max_length=200, null=False)
    description = models.TextField(null=False, blank=True)

    def __str__(self):
        return self.code
    
# BUILDUP: UNCOMMENT:
# TO DO: 
# class PassimRun(models.Model):
#     """Describes a passim run"""
#     name = models.CharField(max_length=25, null=False)
#     parameters = models.CharField(max_length=200, null=False)
#     date = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
#     release = models.ForeignKey("ReleaseInfo", blank=False, 
#                                 related_name='passim_runs', related_query_name="passim_run",
#                                 on_delete=models.DO_NOTHING) # e.g., 2021.2.5
#     description = models.TextField(null=False, blank=True)
#     runtype = models.CharField(max_length=25, null=False) # pri, all, versions

#     def __str__(self):
#         return self.name

