"""THIS SCRIPT IS WORK IN PROGRESS - DO NOT USE YET

This script uploads the metadata of a single release to the database.

Provide the relevant inputs for the script in the Command.handle() function: e.g., 
    release_code = "2022.1.6"
    release_date = datetime.date(2022, 7, 8) # YYYY, M, D
    meta_fp = "meta/OpenITI_metadata_2022-1-6_wNoor.csv"
    base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.1.6/data"
    zenodo_link = "https://zenodo.org/record/6808108"
    release_notes_fp = "meta/release_notes_2022-1-6.txt"
    reuse_data_fp = "reuse_data/stats-v2022-1-6_bi-dir.csv"
    reuse_data_base_url = "http://dev.kitab-project.org/passim01102022/"

NB: for the metadata file, use the _wNoor version, non-merged.

"""

import csv
from webbrowser import get
from django.db import models

#from api.models import CorpusInsights, TextReuseStats, 
from api.models import Author, Text, Version, Edition, \
    ReleaseVersion, SourceCollectionDetails, \
    Date, DateType, Calendar, DateLink,\
    ObjectName, ObjectNameLink, A2BRelation, RelationType, \
    TextType, TextTypeLink, ReleaseInfo, \
    ManuscriptHolding, Place, Manuscript, \
    ExternalID, ExternalIDLink, IdentifierProvider
from django.core.management.base import BaseCommand
import re
import datetime
import json
import traceback
from decimal import Decimal


from openiti.helper.ara import normalize_ara_light
from api.util.betacode import betacodeToSearch, betacodeToArabic
from api.util.utility import compute_ce_range, COUNTRY_CODES

from itertools import islice

VERSION_CODES = dict()  # NOT USED??
VERBOSE = True
DATE_TYPES = {}
CALENDARS = {}

with open("meta/alThurayya_places.json", encoding="utf-8") as file:
    data = json.load(file)
    ALTHURAYYA_LOOKUP = {d["properties"]["cornuData"]["cornu_URI"]: d["properties"]["cornuData"] for d in data["features"]}

class Command(BaseCommand):
    def handle(self, **options):
        # if testing, only upload text reuse data for Tabari.Tarikh and MalikIbnAnas.Muwatta
        test = True

        # if uploading only text reuse stats: set upload to False:
        meta_upload=True

        imported_models = [ObjectNameLink, A2BRelation, DateLink, TextTypeLink,\
                           ReleaseInfo, Calendar, DateType, RelationType, TextType, Edition,\
                           Version, ReleaseVersion, SourceCollectionDetails,\
                           ObjectName, Date, Author, Text
                          ]
        # for m in imported_models:
        #     print(m)
        #     try:
        #         m.objects.all().delete()
        #     except Exception as e:
        #         print("Failed to delete data:", e)
        # input("CONTINUE?")
        
        

        #TextReuseStats.objects.all().delete()

        # provide the release details here:

        release_code = "2025.1.9"
        release_date = datetime.date(2025, 12, 30) # YYYY, M, D
        meta_fp = "meta/OpenITI_metadata_2025-1-9_wNoor.csv"
        base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2025.1.9/data"
        zenodo_link = "https://zenodo.org/records/17767721"
        release_notes_fp = "meta/release_notes_2025-1-9.txt"
        reuse_data_fp = None
        #reuse_data_base_url = "http://dev.kitab-project.org/2023.1.8/"
        reuse_data_base_url = "http://dev.kitab-project.org/2025.1.9-pairwise/"


        # release_code = "2023.1.8"
        # release_date = datetime.date(2023, 10, 17) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2023-1-8_wNoor.csv"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2023.1.8/data"
        # zenodo_link = "https://zenodo.org/records/10007820"
        # release_notes_fp = "meta/release_notes_2023-1-8.txt"
        # reuse_data_fp = "reuse_data/stats-v8_uni-dir.csv"
        # #reuse_data_base_url = "http://dev.kitab-project.org/2023.1.8/"
        # reuse_data_base_url = "http://dev.kitab-project.org/2023.1.8-pairwise/"


        # release_code = "2022.2.7"
        # release_date = datetime.date(2023, 2, 24) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2022-2-7_wNoor.csv"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.2.7/data"
        # zenodo_link = "https://zenodo.org/record/7687795"
        # release_notes_fp = "meta/release_notes_2022-2-7.txt"
        # reuse_data_fp = "reuse_data/stats-v2022-2-7_bi-dir.csv"
        # #reuse_data_base_url = "http://dev.kitab-project.org/passim01122022-v7/"
        # reuse_data_base_url = "http://dev.kitab-project.org/2022.2.7-pairwise/"

        # release_code = "2022.1.6"
        # release_date = datetime.date(2022, 7, 8) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2022-1-6_wNoor.csv"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.1.6/data"
        # zenodo_link = "https://zenodo.org/record/6808108"
        # release_notes_fp = "meta/release_notes_2022-1-6.txt"
        # reuse_data_fp = "reuse_data/stats-v2022-1-6_bi-dir.csv"
        # #reuse_data_base_url = "http://dev.kitab-project.org/passim01102022/"
        # reuse_data_base_url = "http://dev.kitab-project.org/2022.1.6-pairwise/"

        # release_code = "2021.2.5"
        # release_date = datetime.date(2021, 10, 18) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2021-2-5_wNoor.csv"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2021.2.5/data"
        # zenodo_link = "https://zenodo.org/record/5550338"
        # release_notes_fp="meta/release_notes_2021-2-5.txt"
        # reuse_data_fp = "reuse_data/stats-v2021-2-5_bi-dir.csv"
        # #reuse_data_base_url = "http://dev.kitab-project.org/passim01102021/"
        # reuse_data_base_url = "http://dev.kitab-project.org/2021.2.5-pairwise/"


        # release_code = "2021.1.4"
        # release_date = datetime.date(2021, 2, 5) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2021-1-4_merged_wNoor.csv"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2021.1.4/data"
        # zenodo_link = "https://zenodo.org/record/4513723"
        # release_notes_fp="meta/release_notes_2021-1-4.txt"
        # reuse_data_fp = "reuse_data/stats-v2021-1-4_bi-dir.csv"
        # reuse_data_base_url = "http://dev.kitab-project.org/passim01022021/"

        with open(release_notes_fp, mode="r", encoding="utf-8") as file:
            release_notes = file.read()

        release_info = dict(
            release_code=release_code,
            release_date=release_date,
            zenodo_link=zenodo_link,
            release_notes=release_notes,
        )

        main(meta_fp, base_url, release_info, reuse_data_fp, reuse_data_base_url, test=test, meta_upload=meta_upload)


def main(meta_fp, base_url, release_info, reuse_data_fp, reuse_data_base_url, test=False, meta_upload=True):
    # load the release metadata:
    release_obj, version_codes_d = upload_release_meta(meta_fp, base_url, release_info, meta_upload=meta_upload, test=test)
    
    # BUILDUP: UNCOMMENT:
    # # check for duplicate version_codes:
    # print("-"*60)
    # no_duplicates=True
    # for version_code, fn_list in VERSION_CODES.items():
    #     if len(fn_list) > 1:
    #         print("DUPLICATE ID:", version_code)
    #         print(fn_list)
    #         no_duplicates = False
    # if no_duplicates:
    #     print("No duplicate version IDs found")
    # print("-"*60)

    
    # # upload the text reuse stats:
    # upload_reuse_stats(reuse_data_fp, release_info["release_code"], release_obj, reuse_data_base_url, version_codes_d, test=test)
    
    # # create the corpus insights data:
    # # TO DO
    

def get_version_lang(version_uri):
    try:
        return re.findall("-([a-z]{3})", version_uri)[0]
    except:
        return ""
    
def get_annotation_status(value):
    if value == 'mARkdown' or value == 'completed' or value == 'inProgress':
        return value
    else:
        #return 'notYetAnnotated'
        return "(not yet annotated)"

# def ah2ce(date):
#     """convert AH date to CE date"""
#     return 622 + (int(date) * 354 / 365.25)

def get_city_from_loc_uri(loc_uri):
    if not re.findall(r"^MS\d{4}", loc_uri):
        return ""
    # build the city, character by character,
    # starting from the character after the 
    city = loc_uri[6]
    for char in loc_uri[7:]:
        if char.isupper(): # start of a new word in the URI
            if city not in ("Los", "St", "Saint", "New", "San", "Al", "El"):
                return city
        city += char
    return ""

def get_or_create_country_obj(country_code):
    
    if country_code not in COUNTRY_CODES:
        print("UNKNOWN COUNTRY CODE:", country_code)
        return None
    else:
        # if the country does not yet exist in the database, create it:
        country_obj = COUNTRY_CODES[country_code]["db_object"]
        if not country_obj:
            # create the country object in the database:
            country_obj = Place.objects.create(
                code=country_code,
                country_code=country_code
            )
        
            # add the country name in the database:
            country_name = COUNTRY_CODES[country_code]["name"]
            nm = get_or_create_name_obj(country_name, "EN", "country_name")
            link_name_to_obj(nm, place_obj=country_obj, is_preferred=True)

            # store the object for later use:
            COUNTRY_CODES[country_code]["db_object"] = country_obj
    
    return country_obj
    


def get_or_create_place_obj(place_code, part_of_obj, thurayya_uri=False):
    """Get a place object from the database, or create it if it does not exist
    
    Args:
        place_code (str): the unique code for a place object
        part_of_obj (obj): generic relation type for hierarchy of places
        thurayya_uri (bool): if True, the place_code is a Thurayya URI
    """
    pm, created = Place.objects.get_or_create(
        code=place_code
    )
    # if it already existed, return the reference to the object:
    if not created:
        return pm
    
    elif thurayya_uri:
        # get the coordinates and names from the Thurayya dataset
        # and upload them to the database
        d = ALTHURAYYA_LOOKUP[thurayya_uri]

        # add the coordinates:
        lat_str = d["coord_lat"]
        lon_str = d["coord_lon"]
        if lat_str:
            pm.lat = Decimal(lat_str)
        if lon_str:
            pm.lon = Decimal(lon_str)
        if lat_str and lon_str:
            if lat_str.startswith("-"):
                lat_letter = "W"
            else:
                lat_letter = "E"
            if lon_str.startswith("-"):
                lon_letter = "S"
            else: 
                lon_letter = "N"
            pm.coordinates_str = f"{lat_str}{lat_letter}, {lon_str}{lon_letter}"
        
        # add the preferred Arabic name:
        name_ar_prefered = d["toponym_arabic"]
        nm = get_or_create_name_obj(name_ar_prefered, "AR", "toponym")
        link_name_to_obj(nm, place_obj=pm, is_preferred=True)
        
        # add alternative Arabic names:
        for name in re.split(" *، *", d["toponym_arabic_other"]):
            # do not duplicate the prefered name:
            if name == name_ar_prefered:
                continue
            nm = get_or_create_name_obj(name, "AR", "toponym")
            link_name_to_obj(nm, place_obj=pm, is_preferred=False)
        
        # add the preferred Latin name:
        name_lat_prefered = d["toponym_translit"]
        nm = get_or_create_name_obj(name_lat_prefered, "LAT", "toponym")
        link_name_to_obj(nm, place_obj=pm, is_preferred=True)
        
        # add alternative Latin names:
        for name in re.split(" *، *", d["toponym_translit_other"]):
            # do not duplicate the prefered name:
            if name == name_lat_prefered:
                continue
            nm = get_or_create_name_obj(name, "LAT", "toponym")
            link_name_to_obj(nm, place_obj=pm, is_preferred=False)
        
        # create the region name if it does not exist yet:
        region_code = d["region_code"]
        rm, region_created = Place.objects.get_or_create(
            code=region_code
        )
        if region_created:
            # Add the Latin region name:
            region_lat = betacodeToSearch(d["region_spelled"])
            nm = get_or_create_name_obj(region_lat, "LAT", "toponym")
            link_name_to_obj(nm, place_obj=rm, is_preferred=True)

            # Add the Arabic region name:
            region_ar = betacodeToArabic(d["region_spelled"])
            nm = get_or_create_name_obj(region_ar, "AR", "toponym")
            link_name_to_obj(nm, place_obj=rm, is_preferred=True)

        # link the place to the region:
        link_places(pm, rm, part_of_obj)

    

    return pm

def get_or_create_name_obj(name, language, name_type):
    if not name:
        return
    """Create name objects for authors and link them to the author object"""
    #print("Create ObjectName object for", name)
    # generate a normalized version of the name:
    if language.upper() in ("ARA", "AR"):
        normalized_name = normalize_ara_light(name)
    elif language.upper() in ("LAT", "EN"):
        normalized_name = betacodeToSearch(name)
    else:
        normalized_name = name
    
    # create the name object:
    nm, _created = ObjectName.objects.get_or_create(
        name=name,
        normalized_name=normalized_name,
        language=language,
        name_type=name_type
    )
    #print("Object created:", nm)
    return nm

# def link_author_name(am, nm, is_preferred=False, source=""):
#     if nm is None:
#         return
#     #print("Linking name object", nm, "to author object", am)
#     # create the link between author name and name object:
#     link, link_created = ObjectNameLink.objects.get_or_create(
#         author=am,
#         object_name=nm,
#         source=source,
#         defaults={"is_preferred": is_preferred}
#     )
#     # if the link already existed but was not preferred until now, make it preferred:
#     if is_preferred and not link_created and not link.is_preferred:
#         link.is_preferred = True
#         link.save(update_fields=["is_preferred"])

def link_name_to_obj(name_obj, author_obj=None, text_obj=None, 
                     loc_obj=None, place_obj=None, manuscr_obj=None, is_preferred=False, source=""):
    if name_obj is None:
        return
    #print("Linking name object", nm, "to other object", (author_obj or text_obj))
    # create the link between name object and other object:
    link, link_created = ObjectNameLink.objects.get_or_create(
        author=author_obj,
        text=text_obj,
        place=place_obj,
        manuscript_holding=loc_obj,
        manuscript=manuscr_obj,
        object_name=name_obj,
        source=source,
        defaults={"is_preferred": is_preferred}
    )
    # if the link already existed but was not preferred until now, make it preferred:
    if is_preferred and not link_created and not link.is_preferred:
        link.is_preferred = True
        link.save(update_fields=["is_preferred"])

def link_book_to_author(text_obj, author_obj, rel_type_obj, authority=""):
    rel, created = A2BRelation.objects.get_or_create(
        person_a=author_obj,
        text_b=text_obj,
        relation_type=rel_type_obj,
        authority=authority
    )

def link_manuscript_to_author(ms_obj, record, rel_type_obj, 
                              failed_dates, authority=""):
    author_obj = get_or_create_author(record, failed_dates)
    rel, created = A2BRelation.objects.get_or_create(
        person_a=author_obj,
        manuscript_b=ms_obj,
        relation_type=rel_type_obj,
        authority=authority
    )

def link_manuscript_to_texts(ms_obj, record, rel_type_obj, authority=""):
    """Link a  manuscript object to text_uris of texts inside it"""
    for text_uri, page_range in record["text_uris"]:
        print("RELATED TEXT URI:", text_uri)
        if page_range:
            page_range = "Page range: " + page_range
        else:
            page_range = ""
        # get or create the text object in the database:
        tm, tm_created = Text.objects.get_or_create(
            text_uri=text_uri,
            defaults={
                "notes": page_range
            }
        )
        rel, created = A2BRelation.objects.get_or_create(
            manuscript_a=ms_obj,
            text_b=tm,
            relation_type=rel_type_obj,
            authority=authority
        )

def link_manuscript_to_dates(ms_obj, record, source=""):
    # TODO: when loading metadata from YML files, 
    # parse the 30#MS#DATE#AH####: key
    if "dates" not in record:
        return
    try:
        dd, mm, yyyy = date.split("-")
        try: 
            dd = int(dd)
        except:
            dd = None
        try: 
            mm = int(mm)
        except:
            mm = None
        try:
            yyyy = int(yyyy)
        except:
            yyyy = None
    except:
        dd = None
        mm = None
        yyyy = None
    for date, page_range in record["dates"]:
        date_obj = get_or_create_date(
            date_type_slug="date_written",
            calendar_slug="hijri",
            date_str=date,
            year=yyyy,
            month=mm,
            day=mm,
            source=source,
        )

def link_manuscript_to_whole(holding_obj, ms_obj, record, rel_type_obj, authority=""):
    if "ms_part_of" in record:
        parent_uri = record["ms_part_of"]
        print("PARENT URI:", parent_uri)
        parent_obj, created = Manuscript.objects.get_or_create(
            manuscript_uri=parent_uri,
            manuscript_holding=holding_obj
        )
        
        rel, created = A2BRelation.objects.get_or_create(
            manuscript_a=ms_obj,
            manuscript_b=parent_obj,
            relation_type=rel_type_obj,
            authority=authority
        )

def link_places(place_a, place_b, rel_type_obj, authority=""):
    if not (place_a and place_b):
        print("None-existent place:")
        print("- place_a:", place_a)
        print("- place_b:", place_b)
        return
    rel, created = A2BRelation.objects.get_or_create(
        place_a=place_a,
        place_b=place_b,
        relation_type=rel_type_obj,
        authority=authority
    )


def link_manuscript_to_titles(mm, record):
    """Add various titles to a manuscript object"""
    for name in record['titles_ar'].split(" :: "):
        nm = get_or_create_name_obj(name, "AR", "title")
        link_name_to_obj(nm, manuscr_obj=mm, is_preferred=False)
    for name in record['titles_lat'].split(" :: "):
        nm = get_or_create_name_obj(name, "LAT", "title")
        link_name_to_obj(nm, manuscr_obj=mm, is_preferred=False)
    name = record['title_ar_prefered']
    nm = get_or_create_name_obj(name, "AR", "title")
    link_name_to_obj(nm, manuscr_obj=mm, is_preferred=True)
    name = record['title_lat_prefered']
    nm = get_or_create_name_obj(name, "LAT", "title")
    link_name_to_obj(nm, manuscr_obj=mm, is_preferred=True)

def link_book_to_titles(tm, record):
    """Add various titles to a book/text object"""
    for name in record['titles_ar'].split(" :: "):
        nm = get_or_create_name_obj(name, "AR", "title")
        link_name_to_obj(nm, text_obj=tm, is_preferred=False)
    for name in record['titles_lat'].split(" :: "):
        nm = get_or_create_name_obj(name, "LAT", "title")
        link_name_to_obj(nm, text_obj=tm, is_preferred=False)
    name = record['title_ar_prefered']
    nm = get_or_create_name_obj(name, "AR", "title")
    link_name_to_obj(nm, text_obj=tm, is_preferred=True)
    name = record['title_lat_prefered']
    nm = get_or_create_name_obj(name, "LAT", "title")
    link_name_to_obj(nm, text_obj=tm, is_preferred=True)
    
def add_book_type(text_obj, text_type_obj, is_preferred=False,
                  note="", source=""):
    link, link_created = TextTypeLink.objects.get_or_create(
        text_type=text_type_obj,
        text=text_obj,
        source=source,
        defaults={
            "is_preferred": is_preferred, 
            "note": note
        }
    )
    # if the link already existed but was not preferred until now, make it preferred:
    if is_preferred and not link_created and not link.is_preferred:
        link.is_preferred = True
        link.save(update_fields=["is_preferred"])

def add_holding_names(hm, record):
    """Add various names to a manuscript holding object"""
    for name in record['institution_ar'].split(" :: "):
        nm = get_or_create_name_obj(name, "AR", "institution_name")
        link_name_to_obj(nm, loc_obj=hm, is_preferred=False)
    for name in record['institution_lat'].split(" :: "):
        nm = get_or_create_name_obj(name, "LAT", "institution_name")
        link_name_to_obj(nm, loc_obj=hm, is_preferred=False)

def add_city_names(city_obj, record):
    """Add various names to a manuscript holding object"""
    for name in record['city_ar'].split(" :: "):
        nm = get_or_create_name_obj(name, "AR", "city_name")
        link_name_to_obj(nm, place_obj=city_obj, is_preferred=False)
    for name in record['city_lat'].split(" :: "):
        nm = get_or_create_name_obj(name, "LAT", "city_name")
        link_name_to_obj(nm, place_obj=city_obj, is_preferred=False)

def add_author_names(am, record):
    """Add various names to an author object"""
    for name in record['author_ar'].split(" :: "):
        nm = get_or_create_name_obj(name, "AR", "full_name")
        #link_author_name(am, nm, is_preferred=False)
        link_name_to_obj(nm, author_obj=am, is_preferred=False)
    for name in record['author_lat'].split(" :: "):
        nm = get_or_create_name_obj(name, "LAT", "full_name")
        #link_author_name(am, nm, is_preferred=False)
        link_name_to_obj(nm, author_obj=am, is_preferred=False)
    for name in record['author_ar_prefered'].split(" :: "):
        nm = get_or_create_name_obj(name, "AR", "full_name")
        #link_author_name(am, nm, is_preferred=True)
        link_name_to_obj(nm, author_obj=am, is_preferred=True)
    for name in record['author_lat_prefered'].split(" :: "):
        nm = get_or_create_name_obj(name, "LAT", "full_name")
        #link_author_name(am, nm, is_preferred=True)
        link_name_to_obj(nm, author_obj=am, is_preferred=True)
    
    name = record['author_lat_shuhra']
    nm = get_or_create_name_obj(name, "LAT", "shuhra")
    #link_author_name(am, nm, is_preferred=False)
    link_name_to_obj(nm, author_obj=am, is_preferred=False)
    
    name = record['author_from_uri']
    nm = get_or_create_name_obj(name, "LAT", "full_name")
    #link_author_name(am, nm, is_preferred=False, source="URI")
    link_name_to_obj(nm, author_obj=am, is_preferred=True, source="URI")

def get_or_create_date(date_type_slug, calendar_slug, date_str,
                       year=None, month=None, day=None, precision="year",
                       source="", confidence=None):
    """
    get or create a Date object in the database
    """
    ce_start, ce_end = compute_ce_range(calendar_slug, year, precision=precision)
    try:
        dt = DATE_TYPES[date_type_slug]
    except:
        dt, created = DateType.objects.get_or_create(
            slug=date_type_slug,
            label=date_type_slug
        )
        DATE_TYPES[date_type_slug] = dt
    try:
        cal = CALENDARS[calendar_slug]
    except:
        cal, created = Calendar.objects.get_or_create(
            slug=calendar_slug,
            name=calendar_slug
        )
        CALENDARS[calendar_slug] = cal

    try:
        #print([ce_start, ce_end, dt, cal])
        obj, _created = Date.objects.get_or_create(
        date_type=dt,
        calendar=cal,
        date_str=date_str,
        defaults=dict(
            year=year,
            month=month,
            day=day,
            precision=precision,
            ce_start=ce_start,
            ce_end=ce_end,
            source=source,
            confidence=confidence,
            ),
        )
    except Exception as e: 
        print("CREATING DATE OBJECT FAILED:", e)
        print(traceback.format_exc())
        print(dict(
            date_type=dt,
            calendar=cal,
            date_str=date_str,
            year=year,
            month=month,
            day=day,
            precision=precision,
            ce_start=ce_start,
            ce_end=ce_end,
            source=source,
            confidence=confidence,
            ))
        return None
    return obj

def add_worldcat_id(edition_obj, record, worldcat_obj):
    if "worldcat_links" not in record:
        return
    if record['worldcat_links'] == []:
        return
    for link in record['worldcat_links']:
        try:
            # get the numerical worldcat ID from the URL:
            worldcat_id = re.findall(r"\d+", link)[-1]
        except:
            print("NO WORLDCAT ID FOUND in", link)
            input("CONTINUE?")
            return
        
        # create the external ID
        id_obj, created = ExternalID.objects.get_or_create(
            provider=worldcat_obj,
            external_id=worldcat_id
        )

        # link the edition to the external ID:
        rel, created = ExternalIDLink.objects.get_or_create(
            identifier=id_obj,
            edition=edition_obj
        )



def attach_dates_to_author(author, date_objs):
    """
    Bulk-create DateLink rows (safe with through model).
    """
    links = [DateLink(date=d, author=author) for d in date_objs]
    DateLink.objects.bulk_create(links, ignore_conflicts=True)

def split_tag_list(tag_list):
    version_tags = []
    text_tags = []
    author_tags = []
 
    for tag in tag_list:
        if "MARKDOWN" in tag:
            version_tags.append("MARKDOWN")
        elif "COMPLETED" in tag:
            version_tags.append("COMPLETED")
        elif "INPROGRESS" in tag:
            version_tags.append("INPROGRESS")
        elif "CLEANED_VERSION" in tag:
            version_tags.append("CLEANED_VERSION")
        elif "NO_MAJOR_ISSUES" in tag:
            version_tags.append("NO_MAJOR_ISSUES")
        #elif "born@" in tag or "died@" in tag or "resided@" in tag or "visited@" in tag:
        elif re.findall("born@|died@|resided@|visited@", tag):
            author_tags.append(tag)
        elif "@" in tag or tag.startswith("_"):
            text_tags.append(tag)
        else:
            version_tags.append(tag)
    return version_tags, text_tags, author_tags

def clean(s):
    s = re.sub(" *¶ *", " ", s)
    return s.strip()
        
def format_fields(data, base_url):
    record = dict()
    
    record['version_uri'] = data['versionUri']


    # TODO: deal with multi-language items!
    if "language" in data:
        record['version_lang'] = data['language']
    else:
        record['version_lang'] = get_version_lang(record['version_uri'])
    
    if data['date']:
        date = int(data['date'])
    else:
        date = None
    record['date'] = date
    record['date_AH'] = date
    record['date_CE'] = None
    record['date_str'] = date
    # add normalized versions + prefered version of the arabic-script author name:
    author_ar = re.split(' *:: *| *, *| *; *', clean(data['author_ar']))
    #normalized_author_ar = [normalize_ara_light(clean(a)) for a in author_ar if a]
    #record['author_ar'] = " :: ".join(list(set(author_ar + normalized_author_ar)))
    record['author_ar'] = " :: ".join(list(set(author_ar)))
    record['author_ar_prefered'] = author_ar[0]
    # add normalized versions + prefered version of the latin-script author name:
    author_lat_shuhra = re.split(' *:: *| *, *| *; *', clean(data['author_lat_shuhra']))
    author_lat = re.split(' *:: *| *, *| *; *', clean(data['author_lat']))
    if data['author_lat_shuhra']:
        record['author_lat_prefered'] = author_lat_shuhra[0]
    else:
        record['author_lat_prefered'] = author_lat[0]
    author_lat += author_lat_shuhra
    #normalized_author_lat = [betacodeToSearch(a) for a in author_lat if a]
    #record['author_lat'] = " :: ".join(list(set(author_lat + normalized_author_lat)))
    record['author_lat'] = " :: ".join(list(set(author_lat)))

    record['text_uri'] = data['book']
    record['author_uri'] = data['book'].split(".")[0]

    # add normalized version of the Arabic-script titles:
    titles_ar = re.split(' *:: *| *, *| *; *', clean(data['title_ar']))
    #normalized_titles_ar = [normalize_ara_light(clean(t)) for t in titles_ar if t]
    #record['titles_ar'] = " :: ".join(list(set(titles_ar + normalized_titles_ar)))
    record['titles_ar'] = " :: ".join(list(set(titles_ar)))
    # add normalized version of the Latin-script titles:
    titles_lat = re.split(' *:: *| *, *| *; *', clean(data['title_lat']))
    #normalized_titles_lat = [betacodeToSearch(t) for t in titles_lat if t]
    #record['titles_lat'] = " :: ".join(list(set(titles_lat + normalized_titles_lat)))
    record['titles_lat'] = " :: ".join(list(set(titles_lat)))

    # define the preferred title: 
    record['title_ar_prefered'] = titles_ar[0]
    record['title_lat_prefered'] = titles_lat[0]

    record['ed_info'] = clean(data['ed_info'])
    if "worldcat.org" in record['ed_info']:
        ed_info = []
        worldcat_links = []
        for el in record['ed_info'].split(" :: "):
            if "worldcat.org" in el:
                worldcat_links.append(el)
            elif el.strip():
                ed_info.append(el)
        record['ed_info'] = " :: ".join(ed_info)
        record["worldcat_links"] = worldcat_links
    record['version_code'] = data['id']

    # check if the version is part of a text file that was split because of its size:
    if re.findall("[A-Z]$", data['id']):
        record["part_of"] = data['id'][:-1]
        print(data['id'], "is part of", data['id'][:-1])

    try:
        record["collection_code"] = re.findall(r"^([A-Za-z]+?\d*[A-Za-z]+)\d+(?:BK\d+)?(?:Vols)?[A-Z]?$", data['id'])[0]
    except:
        record["collection_code"] = None
        print("Collection code not found in", data['id'])
    version_tags, text_tags, author_tags = split_tag_list(data['tags'].split(" :: "))
    record["version_tags"] = " :: ".join([t for t in version_tags if t])
    record["text_tags"] = " :: ".join([t for t in text_tags if t])
    record["author_tags"] = " :: ".join([t for t in author_tags if t])
    

    record['author_from_uri'] = data['author_from_uri']
    record['author_lat_shuhra'] = data['author_lat_shuhra']
    record['author_lat_full_name'] = clean(data['author_lat_full_name'])

    ##releasefields
    record['char_length'] = data['char_length']
    record['tok_length'] = data['tok_length']
    # record['url'] = data['url'].replace("../data", base_url)  # this creates problems with v2022.2.7, which has ../data/xxxxAH/data/
    record['url'] = re.sub( ".{,15}/data", base_url, data['url'])   # greedy quantifier `{,}` deals with both situations: ../data/ and ../data/xxxxAH/data/
    record['analysis_priority'] = data['status']
    record['annotation_status'] = get_annotation_status(data['url'].split('.')[-1])
    if "type" in data:
        record["type"] = data["type"]
    else:
        record["type"] = "book"

    ##manuscriptfields:
    ms_keys = ['city_ar', 'city_lat', 'institution_ar', 'institution_lat', 
               'catalog_ref', 'shelfmark']
    for k in ms_keys:
        if k in data:
            record[k] = data[k]
        else:
            record[k] = ""
    
    manuscript_uri = ".".join(data["versionUri"].split(".")[:2])
    record["manuscript_uri"] = manuscript_uri

    if "uncorrected_OCR" in data:
        if data["uncorrected_OCR"] in ("FALSE", "False", False):
           record["uncorrected_OCR"] = False
        elif data["uncorrected_OCR"] in ("TRUE", "True", True):
           record["uncorrected_OCR"] = True
        else:
            print("Unexpected value for 'uncorrected_OCR':", repr(data["uncorrected_OCR"]))
            record["uncorrected_OCR"] = None
    else:
        if "UNCORRECTED_OCR" in data["tags"]:
            record["uncorrected_OCR"] = True
        else:
            record["uncorrected_OCR"] = None            

    if "subcorpus" in data:
        record["subcorpus"] = data["subcorpus"]
    else:
        record["subcorpus"] = record['version_lang']

    # deal with manuscripts that contain one or more specific texts:
    record["text_uris"] = []
    if "parts" in data:
        for part in re.split(" *[;,:]+ *", data["parts"]):
            if not part:
                continue
            if "@" in part:
                text_uri, page_range = part.split("@")
                record["text_uris"].append((text_uri, page_range))
            else:
                record["text_uris"].append((part, None))

    # check if the manuscript object is part of a complete manuscript:
    if re.findall(r"P\d+[AB]?\d*$", manuscript_uri):
        parent = re.sub(r"P\d+[AB]?\d*$", "", manuscript_uri)
        record["ms_part_of"] = parent
        print(manuscript_uri, "is part of", parent)
    
    return record

def get_or_create_author(record, failed_dates):
    try:
        am = Author.objects.get(
            author_uri=record['author_uri']
        )
        if VERBOSE:
            print("but author does:", record['author_uri'])
    except:
        if VERBOSE:
            print("Author URI not in database either:", record['author_uri'])

        # the author is not yet in the database! Create a new author object:

        am, am_created = Author.objects.get_or_create(
            author_uri=record['author_uri'],
            tags=record['author_tags']
            # do not upload bibliography and notes
        )
        if am_created and VERBOSE:
            print("-> created", record['author_uri'])
    
    # Add names to the author object:
    add_author_names(am, record)
    
    # add dates related to the author:
    # first, create the date itself: 
    date_obj = get_or_create_date(
        date_type_slug="death_date",
        calendar_slug="hijri",
        date_str=record['author_uri'][:4],
        year=record['date'],
        precision="year",
        source="URI",
    )
    # then, add the link to the author:
    if date_obj:
        DateLink.objects.get_or_create(date=date_obj, author=am)
    else:
        failed_dates.add(record['author_uri'][:4])

    return am

def upload_book_corpus_meta(record, authorship_obj, book_type_obj, release_obj, worldcat_obj, failed_dates):
    # check if the version uri is already in the database:

    #if True:  # TO DO replace with the try... except... block when folding in Versions:
    try:
        vm = Version.objects.get(
            version_uri=record['version_uri']
        )
    except Version.DoesNotExist:
        if VERBOSE:
            print(record['version_uri'], "does not exist in the database")

        # if not, check if the text author_uri is in the database:

        am = get_or_create_author(record, failed_dates)

        # try:
        #     am = Author.objects.get(
        #         author_uri=record['author_uri']
        #     )
        #     if VERBOSE:
        #         print("but author does:", record['author_uri'])
        # except:
        #     if VERBOSE:
        #         print("Author URI not in database either:", record['author_uri'])

        #     # the author is not yet in the database! Create a new author object:

        #     am, am_created = Author.objects.get_or_create(
        #         author_uri=record['author_uri'],
        #         tags=record['author_tags']
        #         # do not upload bibliography and notes
        #     )
        #     if am_created and VERBOSE:
        #         print("-> created", record['author_uri'])
        
        # # Add names to the author object:
        # add_author_names(am, record)
        
        # # add dates related to the author:
        # # first, create the date itself: 
        # date_obj = get_or_create_date(
        #     date_type_slug="death_date",
        #     calendar_slug="hijri",
        #     date_str=record['author_uri'][:4],
        #     year=record['date'],
        #     precision="year",
        #     source="URI",
        # )
        # # then, add the link to the author:
        # if date_obj:
        #     DateLink.objects.get_or_create(date=date_obj, author=am)
        # else:
        #     failed_dates.add(record['author_uri'][:4])


        # the author is now in the database, check if the text exists:
        
        try:
            tm = Text.objects.get(
                text_uri=record['text_uri']
            )
            if VERBOSE:
                print("but text does:", record['text_uri'])
        except: 
            # the text is not yet in the database! Create a new text object:
            if VERBOSE:
                print("Text URI not in database either:", record['text_uri'])
            tm, tm_created = Text.objects.update_or_create(
                text_uri=record["text_uri"],
                #author=am,  # we add the author(s) with link_book_to_author
                defaults=dict(
                    tags=record["text_tags"]
                )
            )
            if tm_created and VERBOSE:
                print("-> created", record['text_uri'])
        
        link_book_to_author(tm, am, authorship_obj, authority="URI")
        link_book_to_titles(tm, record)
        add_book_type(tm, book_type_obj, source="URI")


        # now we are sure the author and text exist in the database, create a new version object:

        # (but first, we check if the edition meta object exists or create it)

        try:
            em = Edition.objects.filter(
                text=tm,
                ed_info=record['ed_info']
            )[0]  # more than one edition with the same query criteria may exist!; 
            # NB: .first() returns None if none exists, so it will not trigger the exception
            if VERBOSE:
                print("Edition does exist")
                print("em:", em)
                print()
        except: 
            if VERBOSE:
                print("Neither does the edition exist")

            em, em_created = Edition.objects.update_or_create(
                text=tm,
                ed_info=record["ed_info"],
            )
            # add worldcat link to external_ids:
            add_worldcat_id(em, record, worldcat_obj)
            if em_created and VERBOSE:
                print("-> Created Edition object")

        # now create the new version object:

        # upload the collection code if it doesn't exist yet:
        cm, cm_created = SourceCollectionDetails.objects.get_or_create(
            code=record["collection_code"]
        )

        if "part_of" in record:
            whole_obj = Version.objects.get(version_uri=record["part_of"])
        else:
            whole_obj = None

        vm, vm_created = Version.objects.update_or_create(
            version_code=record["version_code"],
            version_uri=record["version_uri"],
            text=tm,
            language=record["version_lang"],
            defaults=dict(
                edition=em,
                source_coll=cm,
                part_of=whole_obj
            )
        )     
        if vm_created and VERBOSE:
            print("-> created", record['version_uri'])              


    # now that we know that the version object is in the database, 
    # create or update the ReleaseVersion object:
    rvm, rvm_created = ReleaseVersion.objects.update_or_create(
        release_info=release_obj,
        version=vm,
        defaults=dict(
            url=record["url"],
            char_length=record["char_length"],
            tok_length=record["tok_length"],
            analysis_priority=record["analysis_priority"],
            annotation_status=record["annotation_status"],
            tags=record["version_tags"]
        )
    )
    if rvm_created and VERBOSE:
        print("NEW RELEASE VERSION OBJECT CREATED:", rvm)

def upload_ms_corpus_meta(record, authorship_obj, release_obj, part_of_obj, worldcat_obj, failed_dates):
    # check if the version uri is already in the database:
    #print(record)

    try:
        vm = Version.objects.get(
            version_uri=record['version_uri']
        )
    except Version.DoesNotExist:
        if VERBOSE:
            print(record['version_uri'], "does not exist in the database")

        # if not, check if the manuscript holding (loc) is in the database:
        loc_uri = record['version_uri'].split(".")[0]

        try:
            hm = ManuscriptHolding.objects.get(
                loc_uri=loc_uri
            )
            if VERBOSE:
                print("but manuscript holding does:", loc_uri)
        except:
            if VERBOSE:
                print("manuscript holding not in database either:", loc_uri)

            # the manuscript holding is not yet in the database! 
            # Create a new manuscript holding object:

            hm, hm_created = ManuscriptHolding.objects.get_or_create(
                loc_uri=loc_uri
            )
            if hm_created and VERBOSE:
                print("-> created", loc_uri)
        
        # Add names to the ManuscriptHolding object:
        add_holding_names(hm, record)

        # Add city to the ManuscriptHolding object:
        place_code = get_city_from_loc_uri(loc_uri)
        hm.code = place_code
        if place_code:
            city_obj = get_or_create_place_obj(place_code, part_of_obj)
            add_city_names(city_obj, record)
            hm.city = city_obj
            print(place_code, city_obj)
        
        # Add country to the ManuscriptHolding object:
        country_code = loc_uri[2:6]
        country_obj = get_or_create_country_obj(country_code)
        if country_obj:
            print("COUNTRY OBJECT FOR", country_code, country_obj)
            hm.country = country_obj
            hm.save(update_fields=["city", "country"])

            # link the city to the country:
            link_places(city_obj, country_obj, part_of_obj)

            print(country_code, country_obj)        
        
    #     # add dates related to the manuscript:
    #     # first, create the date itself: 
    #     date_obj = get_or_create_date(
    #         date_type_slug="death_date",
    #         calendar_slug="hijri",
    #         date_str=record['author_uri'][:4],
    #         year=record['date'],
    #         precision="year",
    #         source="URI",
    #     )
    #     # then, add the link to the author:
    #     if date_obj:
    #         DateLink.objects.get_or_create(date=date_obj, author=am)
    #     else:
    #         failed_dates.add(record['author_uri'][:4])


        # the manuscript holding is now in the database, 
        # check if the manuscript exists:
        
        try:
            mm = Manuscript.objects.get(
                manuscript_uri=record['manuscript_uri']
            )
            if VERBOSE:
                print("but manuscript does:", record['manuscript_uri'])
        except: 
            # the manuscript is not yet in the database! Create a new Manuscript object:
            if VERBOSE:
                print("Manuscript URI not in database either:", record['manuscript_uri'])
            mm, mm_created = Manuscript.objects.update_or_create(
                manuscript_uri=record["manuscript_uri"],
                defaults=dict(
                    tags=record["text_tags"],
                    manuscript_holding=hm
                )
            )
            if mm_created and VERBOSE:
                print("-> created", record['manuscript_uri'])
        
        link_manuscript_to_titles(mm, record)
        #link_manuscript_to_author(mm, record, authorship_obj, failed_dates)
        link_manuscript_to_texts(mm, record, part_of_obj)
        link_manuscript_to_dates(mm, record)
        link_manuscript_to_whole(hm, mm, record, part_of_obj)


        # now we are sure the manuscript holding and manuscript exist in the database, 
        # create a new version object:

        # # (but first, we check if the edition meta object exists or create it)
        
        # TODO: Add edition object:
        # try:
        #     em = Edition.objects.filter(
        #         text=tm,
        #         ed_info=record['ed_info']
        #     )[0]  # more than one edition with the same query criteria may exist!; 
        #     # NB: .first() returns None if none exists, so it will not trigger the exception
        #     if VERBOSE:
        #         print("Edition does exist")
        #         print("em:", em)
        #         print()
        # except: 
        #     if VERBOSE:
        #         print("Neither does the edition exist")

        #     em, em_created = Edition.objects.update_or_create(
        #         text=tm,
        #         ed_info=record["ed_info"],
        #     )
        #     # add worldcat link to external_ids:
        #     add_worldcat_id(em, record, worldcat_obj)
        #     if em_created and VERBOSE:
        #         print("-> Created Edition object")


        # upload the collection code if it doesn't exist yet:
        cm, cm_created = SourceCollectionDetails.objects.get_or_create(
            code=record["collection_code"]
        )

        # now create the new version object:

        vm, vm_created = Version.objects.update_or_create(
            version_code=record["version_code"],
            version_uri=record["version_uri"],
            manuscript=mm,
            language=record["version_lang"], # TODO switch to language-script combo
            defaults=dict(
                #edition=em,  # TODO
                source_coll=cm,
            )
        )     
        if vm_created and VERBOSE:
            print("-> created", record['version_uri'])              


    # now that we know that the version object is in the database, 
    # create or update the ReleaseVersion object:
    rvm, rvm_created = ReleaseVersion.objects.update_or_create(
        release_info=release_obj,
        version=vm,
        defaults=dict(
            url=record["url"],
            char_length=record["char_length"],
            tok_length=record["tok_length"],
            analysis_priority=record["analysis_priority"],
            annotation_status=record["annotation_status"],
            tags=record["version_tags"]
        )
    )
    if rvm_created and VERBOSE:
        print("NEW RELEASE VERSION OBJECT CREATED:", rvm)

def upload_release_meta(meta_fp, base_url, release_info, meta_upload=True, test=False):
    print(f"Uploading release {release_info['release_code']} metadata...")
    failed_dates = set()

    # first, create the new release itself in the database:

    release_obj, created = ReleaseInfo.objects.update_or_create(
        release_code=release_info["release_code"],
        defaults=dict(
            release_date=release_info["release_date"],
            zenodo_link=release_info["zenodo_link"],
            release_notes=release_info["release_notes"]
        )
    )
    if created and VERBOSE:
        print("NEW RELEASE ENTRY CREATED:", release_obj)

    # Create / get the ID of the generic authorship relation,
    # used to connect books to their authors:
    
    authorship_obj, created = RelationType.objects.get_or_create(
        code="AUTH",
        name="is author of",
        name_inverted="is written by",
        descr="Generic authorship relation between a person and a book",
        entities="person_book"
    )
    if created and VERBOSE:
        print("AUTHORSHIP OBJECT CREATED:", authorship_obj)

    # Create / get the ID of the text_type for a generic book:
    book_type_obj, created = TextType.objects.get_or_create(
        slug="book",
        label="book",
        description="a generic text_type for books in the OpenITI corpus",
    )
    if created and VERBOSE:
        print("BOOK TYPE OBJECT CREATED:", book_type_obj)

    # Create / get the ID of the generic relation between a part and a whole
    part_of_obj, created = RelationType.objects.get_or_create(
        code="PARTOF",
        name="is part of",
        name_inverted="has part",
        descr="Generic relation between a part and a whole",
        entities=""
    )

    # Create/get the ID for Worldcat:
    worldcat_obj, created = IdentifierProvider.objects.get_or_create(
        slug="worldcat",
        name="Worldcat",
        base_url="https://search.worldcat.org/title/"
    )

    version_codes_d = dict()
    fieldnames = ['versionUri', 'date', 
                  'author_ar', 'author_lat', 'book', 'title_ar', 'title_lat', 
                  'ed_info', 'id', 'status', 'tok_length', 
                  'url', 'tags', 
                  'author_from_uri', 'author_lat_shuhra', 'author_lat_full_name', 
                  'char_length']
    if int(release_info["release_code"].split(".")[-1]) >= 9:
        fieldnames = ['versionUri', 
                       'language','subcorpus', 'uncorrected_OCR',                                  # not in previous releases!
                      'date', 'author_ar', 'author_lat', 'book', 'title_ar', 'title_lat',
                      'ed_info', 'id', 'status', 'tok_length', 
                      'char_length',                                                               # different order in previous releases!
                      'url', 'tags', 
                      'author_from_uri', 'author_lat_shuhra', 'author_lat_full_name', 
                      'city_ar', 'city_lat', 'institution_ar', 'institution_lat',                  # not in previous releases!
                      'shelfmark', 'catalog_ref', 'parts']                                         # not in previous releases!
    with open(meta_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
        header = next(reader)
        
        for version_data in reader:
            # add the version_code + extension to the version_codes_d (to create the url to the text reuse data later)
            version_code = version_data["id"]
            try:
                version_codes_d[version_code] = re.findall(version_code+".*", version_data["url"])[0]
                # for text files that were split into parts, add the whole to the dictionary as well:
                if re.findall("[A-Z]$", version_code): 
                    whole_version_code = version_code[:-1]
                    s = version_codes_d[version_code]
                    whole_s = re.sub(version_code, whole_version_code, s)
                    version_codes_d[whole_version_code] = whole_s
                    print("add whole:", whole_version_code, whole_s)
            except: 
                print("version_code", version_code, "not found in url", version_data["url"])
            
            if not meta_upload:
                continue

            # for tests, only upload the metadata for authors 
            # between 300 and 325
            if test:
                #if not version_data["date"]:
                #    continue
                if version_data["date"] and (int(version_data["date"]) < 310 or int(version_data["date"]) > 310):
                    continue

            # read in the metadata for a version and format it:
            record = format_fields(version_data, base_url)
            print(version_data["versionUri"])

            if version_data["versionUri"].startswith("MS"):
                upload_ms_corpus_meta(record, authorship_obj, release_obj, part_of_obj, worldcat_obj, failed_dates)
            else:
                upload_book_corpus_meta(record, authorship_obj, book_type_obj, release_obj, worldcat_obj, failed_dates)
            # # check if the version uri is already in the database:

            # #if True:  # TO DO replace with the try... except... block when folding in Versions:
            # try:
            #     vm = Version.objects.get(
            #         version_uri=record['version_uri']
            #     )
            # except Version.DoesNotExist:
            #     if VERBOSE:
            #         print(record['version_uri'], "does not exist in the database")

            #     # if not, check if the text author_uri is in the database:

            #     try:
            #         am = Author.objects.get(
            #             author_uri=record['author_uri']
            #         )
            #         if VERBOSE:
            #             print("but author does:", record['author_uri'])
            #     except:
            #         if VERBOSE:
            #             print("Author URI not in database either:", record['author_uri'])

            #         # the author is not yet in the database! Create a new author object:

            #         am, am_created = Author.objects.get_or_create(
            #             author_uri=record['author_uri'],
            #             tags=record['author_tags']
            #             # do not upload bibliography and notes
            #         )
            #         if am_created and VERBOSE:
            #             print("-> created", record['author_uri'])
                
            #     # Add names to the author object:
            #     add_author_names(am, record)
                
            #     # add dates related to the author:
            #     # first, create the date itself: 
            #     date_obj = get_or_create_date(
            #         date_type_slug="death_date",
            #         calendar_slug="hijri",
            #         date_str=record['author_uri'][:4],
            #         year=record['date'],
            #         precision="year",
            #         source="URI",
            #     )
            #     # then, add the link to the author:
            #     if date_obj:
            #         DateLink.objects.get_or_create(date=date_obj, author=am)
            #     else:
            #         failed_dates.add(record['author_uri'][:4])


            #     # the author is now in the database, check if the text exists:
                
            #     try:
            #         tm = Text.objects.get(
            #             text_uri=record['text_uri']
            #         )
            #         if VERBOSE:
            #             print("but text does:", record['text_uri'])
            #     except: 
            #         # the text is not yet in the database! Create a new text object:
            #         if VERBOSE:
            #             print("Text URI not in database either:", record['text_uri'])
            #         tm, tm_created = Text.objects.update_or_create(
            #             text_uri=record["text_uri"],
            #             #author=am,  # we add the author(s) with link_book_to_author
            #             defaults=dict(
            #                 tags=record["text_tags"]
            #             )
            #         )
            #         if tm_created and VERBOSE:
            #             print("-> created", record['text_uri'])
                
            #     link_book_to_author(tm, am, authorship_obj, authority="URI")
            #     link_book_to_titles(tm, record)
            #     add_book_type(tm, book_type_obj, source="URI")


            #     # now we are sure the author and text exist in the database, create a new version object:

            #     # (but first, we check if the edition meta object exists or create it)

            #     try:
            #         em = Edition.objects.filter(
            #             text=tm,
            #             ed_info=record['ed_info']
            #         )[0]  # more than one edition with the same query criteria may exist!; 
            #         # NB: .first() returns None if none exists, so it will not trigger the exception
            #         if VERBOSE:
            #             print("Edition does exist")
            #             print("em:", em)
            #             print()
            #     except: 
            #         if VERBOSE:
            #             print("Neither does the edition exist")



            #         em, em_created = Edition.objects.update_or_create(
            #             text=tm,
            #             ed_info=record["ed_info"],
            #         )
            #         # add worldcat link to external_ids:
            #         add_worldcat_id(em, record, worldcat_obj)
            #         if em_created and VERBOSE:
            #             print("-> Created Edition object")

            #     # now create the new version object:

            #     # upload the collection code if it doesn't exist yet:
            #     cm, cm_created = SourceCollectionDetails.objects.get_or_create(
            #         code=record["collection_code"]
            #     )

            #     if "part_of" in record:
            #         whole_obj = Version.objects.get(version_uri=record["part_of"])
            #     else:
            #         whole_obj = None

            #     vm, vm_created = Version.objects.update_or_create(
            #         version_code=record["version_code"],
            #         version_uri=record["version_uri"],
            #         text=tm,
            #         language=record["version_lang"],
            #         defaults=dict(
            #             edition=em,
            #             source_coll=cm,
            #             part_of=whole_obj
            #         )
            #     )     
            #     if vm_created and VERBOSE:
            #         print("-> created", record['version_uri'])              


            # # now that we know that the version object is in the database, 
            # # create or update the ReleaseVersion object:
            # rvm, rvm_created = ReleaseVersion.objects.update_or_create(
            #     release_info=release_obj,
            #     version=vm,
            #     defaults=dict(
            #         url=record["url"],
            #         char_length=record["char_length"],
            #         tok_length=record["tok_length"],
            #         analysis_priority=record["analysis_priority"],
            #         annotation_status=record["annotation_status"],
            #         tags=record["version_tags"]
            #     )
            # )
            # if rvm_created and VERBOSE:
            #     print("NEW RELEASE VERSION OBJECT CREATED:", rvm)
    if failed_dates:
        print("failed dates:")
    for date in failed_dates:
        print(date)

    print("Done uploading metadata!")

    return release_obj, version_codes_d

# BUILDUP: UNCOMMENT:
# def upload_reuse_stats(reuse_data_fp, release_code, release_obj, reuse_data_base_url, version_codes_d, test=False):
#     print("Loading text reuse stats...")
#     book_cache = dict() # to avoid unnecessary lookups in the database
#     batch = []
#     batch_no = 0
#     batch_size = 100
#     with open(reuse_data_fp, 'r', encoding='utf-8') as f:
#         reader = csv.DictReader(f, delimiter='\t')
        
#         for data in reader:
#             if test:
#                 # for testing: only load stats for 
#                 #   * 0179MalikIbnAnas.Muwatta 
#                 #   * 0310Tabari.Tarikhbooks
#                 #   * all books on the first page of the metadata table for each release:
#                 if not (("JK007501" in data['_T1'] or "JK007501" in data['_T2']) \
#                     or ("Shamela0009783" in data['_T1'] or "Shamela0009783" in data['_T2']) \
#                     or ("Shamela0028107" in data['_T1'] or "Shamela0028107" in data['_T2']) \
#                     or ("JK007502" in data['_T1'] or "JK007502" in data['_T2'])\
#                     or ("ShamAY0037936" in data['_T1'] or "ShamAY0037936" in data['_T2'])\
#                     or ("JK007522" in data['_T1'] or "JK007522" in data['_T2'])\
#                     or ("JK007524" in data['_T1'] or "JK007524" in data['_T2'])\
#                     or ("ShamAY0038526" in data['_T1'] or "ShamAY0038526" in data['_T2'])\
#                     or ("JK007525" in data['_T1'] or "JK007525" in data['_T2'])\
#                     or ("JK007523" in data['_T1'] or "JK007523" in data['_T2'])\
#                     or ("JK007526" in data['_T1'] or "JK007526" in data['_T2'])\
#                     or ("ShamAY0038527" in data['_T1'] or "ShamAY0038527" in data['_T2'])\
#                     or ("JK007521" in data['_T1'] or "JK007521" in data['_T2'])\
#                     or ("JK007527" in data['_T1'] or "JK007527" in data['_T2']) \
#                     or ("ShamAY0037906" in data['_T1'] or "ShamAY0037906" in data['_T2']) \
#                     or ("JK007529" in data['_T1'] or "JK007529" in data['_T2'])\
#                     or ("ShamAY0037959" in data['_T1'] or "ShamAY0037959" in data['_T2']) \
#                     ):  
#                     continue
#             version_code1 = data['_T1'].split("-")[0].split(".")[0]
#             version_code2 = data['_T2'].split("-")[0].split(".")[0]

#             # replace the version code of a part with the version code of the whole (should not be necessary):
#             if re.findall("[A-Z]$", version_code1):
#                 print(version_code1, ">", version_code1[:-1])
#                 version_code1 = version_code1[:-1]
#             if re.findall("[A-Z]$", version_code2):
#                 print(version_code2, ">", version_code2[:-1])
#                 version_code2 = version_code2[:-1]

#             # get the last part of the filename (version_code + lang + number + extension),
#             # which form part of the csv URL
#             try:
#                 ref1 = version_codes_d[version_code1]
#                 ref2 = version_codes_d[version_code2]
#             except:
#                 print("FAILED:", version_code1, version_code2)
#                 ref1 = version_code1 + "-ara1"
#                 ref2 = version_code2 + "-ara1"
            
#             if version_code1 in book_cache:
#                 b1 = book_cache[version_code1]
#             else:
#                 b1 = ReleaseVersion.objects.get(
#                     release_info__release_code=release_code,
#                     version__version_code=version_code1
#                 )
#                 book_cache[version_code1] = b1
#             if version_code2 in book_cache:
#                 b2 = book_cache[version_code2]
#             else:
#                 b2 = ReleaseVersion.objects.get(
#                     release_info__release_code=release_code,
#                     version__version_code=version_code2
#                 )
#                 book_cache[version_code2] = b2
            
#             tsv_url = f"{reuse_data_base_url}{ref1}/{ref1}_{ref2}.csv"
            
#             # tr, created = TextReuseStats.objects.update_or_create(
#             #     book_1 = b1,
#             #     book_2 = b2,
#             #     release_info=release_obj,
#             #     defaults=dict(
#             #         tsv_url=tsv_url,
#             #         instances_count=data['instances'],
#             #         book1_words_matched=data['WM1_Total'],
#             #         book2_words_matched=data['WM2_Total'],
#             #         book1_pct_words_matched=data['WM_B1inB2'],
#             #         book2_pct_words_matched=data['WM_B2inB1'],
#             #     )
#             # )
#             #if created and VERBOSE:
#             #    print("NEW TEXT REUSE ENTRY CREATED:", tr)
#             batch.append(TextReuseStats(
#                 book_1 = b1,
#                 book_2 = b2,
#                 release_info=release_obj,
#                 tsv_url=tsv_url,
#                 instances_count=data['instances'],
#                 book1_words_matched=data['WM1_Total'],
#                 book2_words_matched=data['WM2_Total'],
#                 book1_pct_words_matched=data['WM_B1inB2'],
#                 book2_pct_words_matched=data['WM_B2inB1'],
#                 )
#             )
#             if len(batch) == batch_size:
#                 batch_no += 1
#                 print("loading batch no.", batch_no)
#                 TextReuseStats.objects.bulk_create(batch)
#                 batch = []
        
#     # load the remainder of the last batch:
#     if len(batch) > 0:
#         batch_no += 1
#         print("loading batch no.", batch_no)
#         TextReuseStats.objects.bulk_create(batch)
            