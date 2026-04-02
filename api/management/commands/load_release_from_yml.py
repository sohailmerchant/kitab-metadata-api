"""WORK IN PROGRESS, CONVERTING FROM CSV INPUT...

This script uploads the metadata of a single release to the database,
based on a json representation of all yml files in a release.

Provide the relevant inputs for the script in the Command.handle() function: e.g., 
    release_code = "2025.1.9"
    release_date = datetime.date(2025, 12, 30) # YYYY, M, D
    meta_fp = "meta/release-2025_1_9_wNoor.json"
    base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2025.1.9/data"
    zenodo_link = "https://zenodo.org/records/17767721"
    release_notes_fp = "meta/release_notes_2025-1-9.txt"
    reuse_data_fp = None
    reuse_data_base_url = "http://dev.kitab-project.org/2025.1.9-pairwise/"

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
    ExternalID, ExternalIDLink, IdentifierProvider, \
    Language, Script, LanguageScriptCombo, CorpusInsights
from django.core.management.base import BaseCommand
import os
import re
import datetime
import time
import json
import traceback
import logging
from decimal import Decimal


from openiti.helper.ara import normalize_ara_light
from api.util.betacode import betacodeToSearch, betacodeToArSimple
from api.util.utility import compute_ce_range, COUNTRY_CODES, \
                            tags2dic, extract_metadata_from_header, \
                            collect_author_yml_data, collect_text_yml_data,\
                            collect_version_yml_data, collect_loc_yml_data, \
                            collect_manuscr_yml_data, collect_transcr_yml_data, \
                            set_analysis_priority, get_github_issues, \
                            get_city_from_loc_uri, logger

from itertools import islice

# # prepare logger: 
# today = datetime.datetime.today().strftime("%Y-%m-%d")
# log_fp = f'logs/release_upload_{today}.log'
# if os.path.exists(log_fp):
#     with open(log_fp, mode="w", encoding="utf-8") as file:
#         file.write("")
# logging.basicConfig(filename=log_fp, level=logging.NOTSET)
# logger = logging.getLogger()

IMPORT_STATS = dict()
VERSION_CODES = dict()  # NOT USED??
VERBOSE = False
DATE_TYPES = {}

with open("meta/alThurayya_places.json", encoding="utf-8") as file:
    data = json.load(file)
    ALTHURAYYA_LOOKUP = {d["properties"]["cornuData"]["cornu_URI"]: d["properties"]["cornuData"] for d in data["features"]}

with open("meta/lunar_months.csv", encoding="utf-8") as file:
    LUNAR_MONTHS = {d["abbreviation"]: d["number"] for d in csv.DictReader(file)}

CALENDARS = {}
with open("meta/calendars.csv", encoding="utf-8") as file:
    for d in csv.DictReader(file):
        cal, created = Calendar.objects.get_or_create(
            slug=d["slug"],
            defaults=dict(
                name=d["name"],
                description=d["description"]
            )
        )
        if created:
            IMPORT_STATS["calendar"] = IMPORT_STATS.get("calendar", 0) + 1
        CALENDARS[d["slug"]] = cal

LANG_SCRIPT_NAMES = {}  # will be populated in `load_language_codes`
LANG_SCRIPT_DESCR = {}

# load Maxim's tags into a dictionary
#text_tags = tags2dic(tags_fp)
#print("tags loaded for", len(text_tags), "files")

class Command(BaseCommand):
    def handle(self, **options):
        # if testing, only upload text reuse data for Tabari.Tarikh and MalikIbnAnas.Muwatta
        test = False

        # if uploading only corpus insights: set upload to False:
        meta_upload=True

        # provide the release details here:

        releases = [
            dict(
                release_code = "2021.2.5",
                release_date = datetime.date(2021, 10, 18), # YYYY, M, D
                meta_fp = "meta/OpenITI_metadata_2021-2-5_wNoor.json",
                base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2021.2.5/data",
                zenodo_link = "https://zenodo.org/record/5550338",
                release_notes_fp="meta/release_notes_2021-2-5.txt",
                reuse_data_fp = "reuse_data/stats-v2021-2-5_bi-dir.csv",
                #reuse_data_base_url = "http://dev.kitab-project.org/passim01102021/",
                reuse_data_base_url = "http://dev.kitab-project.org/2021.2.5-pairwise/"
            ),
            dict(
                release_code = "2022.1.6",
                release_date = datetime.date(2022, 7, 8), # YYYY, M, D
                meta_fp = "meta/OpenITI_metadata_2022-1-6_wNoor.json",
                base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.1.6/data",
                zenodo_link = "https://zenodo.org/record/6808108",
                release_notes_fp = "meta/release_notes_2022-1-6.txt",
                reuse_data_fp = "reuse_data/stats-v2022-1-6_bi-dir.csv",
                #reuse_data_base_url = "http://dev.kitab-project.org/passim01102022/",
                reuse_data_base_url = "http://dev.kitab-project.org/2022.1.6-pairwise/"
            ),
            dict(
                release_code = "2022.2.7",
                release_date = datetime.date(2023, 2, 24), # YYYY, M, D
                meta_fp = "meta/OpenITI_metadata_2022-2-7_wNoor.json",
                base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.2.7/data",
                zenodo_link = "https://zenodo.org/record/7687795",
                release_notes_fp = "meta/release_notes_2022-2-7.txt",
                reuse_data_fp = "reuse_data/stats-v2022-2-7_bi-dir.csv",
                #reuse_data_base_url = "http://dev.kitab-project.org/passim01122022-v7/",
                reuse_data_base_url = "http://dev.kitab-project.org/2022.2.7-pairwise/"
            ),
            dict(
                release_code = "2023.1.8",
                release_date = datetime.date(2023, 10, 17), # YYYY, M, D
                meta_fp = "meta/OpenITI_metadata_2023-1-8_wNoor.json",
                base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2023.1.8/data",
                zenodo_link = "https://zenodo.org/records/10007820",
                release_notes_fp = "meta/release_notes_2023-1-8.txt",
                reuse_data_fp = "reuse_data/stats-v8_uni-dir.csv",
                #reuse_data_base_url = "http://dev.kitab-project.org/2023.1.8/",
                reuse_data_base_url = "http://dev.kitab-project.org/2023.1.8-pairwise/"
            ),
            dict(
                release_code = "2025.1.9",
                release_date = datetime.date(2025, 12, 30), # YYYY, M, D
                #meta_fp = "meta/OpenITI_metadata_2025-1-9_wNoor.csv",
                meta_fp = "meta/OpenITI_metadata_2025-1-9_wNoor.json",
                base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2025.1.9/data",
                zenodo_link = "https://zenodo.org/records/17767721",
                release_notes_fp = "meta/release_notes_2025-1-9.txt",
                reuse_data_fp = None,
                reuse_data_base_url = "http://dev.kitab-project.org/2025.1.9-pairwise/"
            ),
            # dict(
            #     release_code = "2021.1.4",
            #     release_date = datetime.date(2021, 2, 5), # YYYY, M, D
            #     meta_fp = "meta/OpenITI_metadata_2021-1-4_merged_wNoor.csv",
            #     base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2021.1.4/data",
            #     zenodo_link = "https://zenodo.org/record/4513723",
            #     release_notes_fp="meta/release_notes_2021-1-4.txt",
            #     reuse_data_fp = "reuse_data/stats-v2021-1-4_bi-dir.csv",
            #     reuse_data_base_url = "http://dev.kitab-project.org/passim01022021/"
            # )
        ]

        # release_code = "2025.1.9"
        # release_date = datetime.date(2025, 12, 30) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2025-1-9_wNoor.csv"
        # meta_fp = "meta/OpenITI_metadata_2025-1-9_wNoor.json"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2025.1.9/data"
        # zenodo_link = "https://zenodo.org/records/17767721"
        # release_notes_fp = "meta/release_notes_2025-1-9.txt"
        # reuse_data_fp = None
        # reuse_data_base_url = "http://dev.kitab-project.org/2025.1.9-pairwise/"


        # # release_code = "2023.1.8"
        # # release_date = datetime.date(2023, 10, 17) # YYYY, M, D
        # # meta_fp = "meta/OpenITI_metadata_2023-1-8_wNoor.csv"
        # # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2023.1.8/data"
        # # zenodo_link = "https://zenodo.org/records/10007820"
        # # release_notes_fp = "meta/release_notes_2023-1-8.txt"
        # # reuse_data_fp = "reuse_data/stats-v8_uni-dir.csv"
        # # #reuse_data_base_url = "http://dev.kitab-project.org/2023.1.8/"
        # # reuse_data_base_url = "http://dev.kitab-project.org/2023.1.8-pairwise/"


        # # release_code = "2022.2.7"
        # # release_date = datetime.date(2023, 2, 24) # YYYY, M, D
        # # meta_fp = "meta/OpenITI_metadata_2022-2-7_wNoor.csv"
        # # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.2.7/data"
        # # zenodo_link = "https://zenodo.org/record/7687795"
        # # release_notes_fp = "meta/release_notes_2022-2-7.txt"
        # # reuse_data_fp = "reuse_data/stats-v2022-2-7_bi-dir.csv"
        # # #reuse_data_base_url = "http://dev.kitab-project.org/passim01122022-v7/"
        # # reuse_data_base_url = "http://dev.kitab-project.org/2022.2.7-pairwise/"

        # # release_code = "2022.1.6"
        # # release_date = datetime.date(2022, 7, 8) # YYYY, M, D
        # # meta_fp = "meta/OpenITI_metadata_2022-1-6_wNoor.csv"
        # # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.1.6/data"
        # # zenodo_link = "https://zenodo.org/record/6808108"
        # # release_notes_fp = "meta/release_notes_2022-1-6.txt"
        # # reuse_data_fp = "reuse_data/stats-v2022-1-6_bi-dir.csv"
        # # #reuse_data_base_url = "http://dev.kitab-project.org/passim01102022/"
        # # reuse_data_base_url = "http://dev.kitab-project.org/2022.1.6-pairwise/"

        # # release_code = "2021.2.5"
        # # release_date = datetime.date(2021, 10, 18) # YYYY, M, D
        # # meta_fp = "meta/OpenITI_metadata_2021-2-5_wNoor.csv"
        # # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2021.2.5/data"
        # # zenodo_link = "https://zenodo.org/record/5550338"
        # # release_notes_fp="meta/release_notes_2021-2-5.txt"
        # # reuse_data_fp = "reuse_data/stats-v2021-2-5_bi-dir.csv"
        # # #reuse_data_base_url = "http://dev.kitab-project.org/passim01102021/"
        # # reuse_data_base_url = "http://dev.kitab-project.org/2021.2.5-pairwise/"


        # # release_code = "2021.1.4"
        # # release_date = datetime.date(2021, 2, 5) # YYYY, M, D
        # # meta_fp = "meta/OpenITI_metadata_2021-1-4_merged_wNoor.csv"
        # # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2021.1.4/data"
        # # zenodo_link = "https://zenodo.org/record/4513723"
        # # release_notes_fp="meta/release_notes_2021-1-4.txt"
        # # reuse_data_fp = "reuse_data/stats-v2021-1-4_bi-dir.csv"
        # # reuse_data_base_url = "http://dev.kitab-project.org/passim01022021/"


        # create / update helper objects in the database:
        relations_definitions_fp = "meta/relations_definitions.tsv"
        source_collections_fp = "meta/source_collections.tsv"
        language_codes_fp = "meta/ISO639_language_codes.csv"
        ext_id_providers_fp = "meta/external_id_providers.csv"
        r = prepare(relations_definitions_fp=relations_definitions_fp,
                source_collections_fp=source_collections_fp,
                language_codes_fp=language_codes_fp,
                ext_id_providers_fp=ext_id_providers_fp,
                )
        authorship_obj, book_type_obj, part_of_obj, worldcat_obj = r

        for release_d in releases:
            main(release_d, authorship_obj, book_type_obj, part_of_obj, worldcat_obj,
                 test=test, meta_upload=meta_upload)
        # main(meta_fp, base_url, release_info, relations_definitions_fp, source_collections_fp, 
        #      reuse_data_fp, reuse_data_base_url, test=test, meta_upload=meta_upload)


def prepare(relations_definitions_fp=None, source_collections_fp=None,
            language_codes_fp=None, ext_id_providers_fp=None):
    
    # load the language and script metadata:
    load_language_codes(language_codes_fp)
    # load the relation types into the database:
    load_relations_definitions(relations_definitions_fp)
    # load the (main) source collections into the database:
    load_source_collections(source_collections_fp)
    # load the metadata of the (main) identity providers into the database:
    load_ext_id_providers(ext_id_providers_fp)

    # Create / get the ID of the generic authorship relation,
    # used to connect books to their authors:
    
    authorship_obj, created = RelationType.objects.get_or_create(
        code="AUTH",
        name="is author of",
        name_inverted="is written by",
        descr="Generic authorship relation between a person and a book",
        entities="person_book"
    )
    if created:
        IMPORT_STATS["relationType"] = IMPORT_STATS.get("relationType", 0) + 1
        if VERBOSE:
            print("AUTHORSHIP OBJECT CREATED:", authorship_obj)

    # Create / get the ID of the text_type for a generic book:
    book_type_obj, created = TextType.objects.get_or_create(
        slug="book",
        label="book",
        description="a generic text_type for books in the OpenITI corpus",
    )
    if created:
        IMPORT_STATS["textType"] = IMPORT_STATS.get("textType", 0) + 1
        if VERBOSE:
            print("BOOK TYPE OBJECT CREATED:", book_type_obj)

    # ms_type_obj, created = TextType.objects.get_or_create(
    #     slug="manuscript",
    #     label="manuscript",
    #     description="a generic text_type for handwritten documents in the OpenITI corpus",
    # )
    # if created and VERBOSE:
    #     print("MANUSCRIPT TYPE OBJECT CREATED:", ms_type_obj)

    # Create / get the ID of the generic relation between a part and a whole
    part_of_obj, created = RelationType.objects.get_or_create(
        code="PARTOF",
        name="is part of",
        name_inverted="has part",
        descr="Generic relation between a part and a whole",
        entities=""
    )
    if created:
        IMPORT_STATS["relationType"] = IMPORT_STATS.get("relationType", 0) + 1

    # Create/get the ID for Worldcat:
    worldcat_obj, created = IdentifierProvider.objects.get_or_create(
        slug="worldcat",
        name="Worldcat",
        base_url="https://search.worldcat.org/title/"
    )
    if created:
        IMPORT_STATS["identifierProvider"] = IMPORT_STATS.get("identifierProvider", 0) + 1


    return authorship_obj, book_type_obj, part_of_obj, worldcat_obj

#def main(meta_fp, base_url, release_info, relations_definitions_fp, source_collections_fp, 
#         reuse_data_fp, reuse_data_base_url, test=False, meta_upload=True):
def main(release_d, authorship_obj, book_type_obj, part_of_obj, worldcat_obj,
         test=False, meta_upload=True):
    start = time.time()
    
    release_notes_fp = release_d["release_notes_fp"]
    with open(release_notes_fp, mode="r", encoding="utf-8") as file:
        release_notes = file.read()

    release_info = dict(
        release_code=release_d["release_code"],
        release_date=release_d["release_date"],
        zenodo_link=release_d["zenodo_link"],
        release_notes=release_notes,
    )

    # load the release metadata:
    meta_fp = release_d["meta_fp"]
    base_url = release_d["base_url"]
    release_obj, version_codes_d = upload_release_meta(meta_fp, base_url, 
        release_info, authorship_obj, book_type_obj, part_of_obj, worldcat_obj,
        meta_upload=meta_upload, test=test)
    msg = f'Uploading release {release_d["release_code"]} metadata took {time.time()-start} seconds.'
    logger.info(msg)
    print(msg)
    
    
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
    # # TODO

def load_language_codes(fp):
    if not fp:
        return
    # create a dictionary of all ISO 639 language codes
    all_language_codes = dict()
    with open(fp, encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            d = dict()
            code3 = row["alpha3-b"]
            d["ISO639-3"] = code3
            d["ISO639-1"] = row["alpha2"]
            d["name"] = row["English"]
            all_language_codes[code3] = d
    # add languages that are not in ISO 639:
    fp = r"meta/additional_language_codes.csv"
    with open(fp, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            d = dict()
            code3 = row["code"]
            d["ISO639-3"] = ""
            d["ISO639-1"] = ""
            d["name"] = row["name"]
            all_language_codes[code3] = d

    # create a dictionary of selected ISO 15924 script codes:
    selected_script_codes = dict()
    fp = r"meta/ISO15924_script_codes.csv"
    with open(fp, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            iso_code = row["ISO15924_script_code"]
            selected_script_codes[iso_code] = row

    # upload the relevant language, script and combo codes:
    fp = r"meta/languages_scripts.csv"
    with open(fp, encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            # get or create the language metadata item:
            lang_code = row ["OpenITI_language_code"]
            iso_lang = row["ISO639-3_language_code"]
            if iso_lang not in all_language_codes:
                if lang_code in all_language_codes:
                    msg = f"UNKNOWN ISO CODE {iso_lang}; TRYING LANG_CODE: {lang_code}"
                    print(msg)
                    logger.warning(msg)
                    lang_name = all_language_codes[lang_code]["name"]
                else:
                    msg = f"UNKNOWN LANGUAGE CODES: {iso_lang}, {lang_code}"
                    print(msg)
                    logger.warning(msg)
                    lang_name = ""
                iso_lang_2 = ""
            else:
                lang_name = all_language_codes[iso_lang]["name"]
                iso_lang_2 = all_language_codes[iso_lang]["ISO639-1"]
                
            lm, created = Language.objects.get_or_create(
                code=lang_code,
                iso_639_3=iso_lang,
                iso_639_1=iso_lang_2,
                name=lang_name
            )
            if created:
                IMPORT_STATS["language"] = IMPORT_STATS.get("language", 0) + 1
            # get or create the script metadata item:
            script_code = row ["OpenITI_script_code"]
            iso_script = row["ISO15924_script_code"]
            if iso_script not in selected_script_codes:
                msg = f"UNKNOWN SCRIPT CODE: {iso_script}"
                print(msg)
                logger.warning(msg)
                script_name = ""
                url = ""
            else:
                script_name = selected_script_codes[iso_script]["name"]
                url = selected_script_codes[iso_script]["url"]
            
            sm, created = Script.objects.get_or_create(
                code=script_code,
                iso_15924=iso_script,
                name=script_name
            )
            if created:
                IMPORT_STATS["script"] = IMPORT_STATS.get("script", 0) + 1
            # get or create the language-script combo item:
             
            combo_code = row["code"]
            name = row["name"]
            descr = row["description"]
            cm, created = LanguageScriptCombo.objects.get_or_create(
                code=combo_code,
                language=lm,
                script=sm,
                defaults=dict(
                    name=name,
                    description=descr
                )
            )
            if created:
                IMPORT_STATS["languageScriptCombo"] = IMPORT_STATS.get("languageScriptCombo", 0) + 1
            
            LANG_SCRIPT_NAMES[combo_code] = name
            LANG_SCRIPT_DESCR[combo_code] = descr
            


def load_relations_definitions(fp):
    """Load the definitions of the relation types into the database from a tsv file"""
    if not fp:
        return
    with open(fp, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            if "descr" in row:
                descr = row["descr"]
            else:
                descr = ""
            reltype, created = RelationType.objects.update_or_create(
                # selection keys:
                code=row["code"],
                subtype_code=row["subtype_code"],
                # update keys:
                defaults = dict(
                   name=row["name"],
                   name_inverted=row["name_inverted"],
                   descr=descr
                )
            )
            if created:
                #print(reltype, created)
                IMPORT_STATS["relationType"] = IMPORT_STATS.get("relationType", 0) + 1

def load_source_collections(fp):
    """Load the descriptions of the OpenITI corpus's source collections and contributors to the database"""
    if not fp:
        return
    with open(fp, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            coll, created = SourceCollectionDetails.objects.update_or_create(
                # selection keys:
                code=row["code"],
                # update keys:
                defaults = dict(
                   name=row["name"],
                   url=row["url"],
                   description=row["description"],
                   affiliation=row["affiliation"]
                )
            )
            if created:
                if VERBOSE:
                    print(coll, created)
                IMPORT_STATS["collection"] = IMPORT_STATS.get("collection", 0) + 1

def load_ext_id_providers(fp):
    if not fp:
        return
    with open(fp, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            prov, created = IdentifierProvider.objects.update_or_create(
                slug=row["slug"],
                defaults=dict(
                    name=row["name"],
                    base_url=row["base_url"]
                )
            )
            if created:
                IMPORT_STATS["identifierProvider"] = IMPORT_STATS.get("identifierProvider", 0) + 1

# def get_version_lang(version_uri):
#     try:
#         return re.findall(r"-(?:([a-z]{3})\d)+", version_uri)[0]
#     except:
#         msg = f"no language found in {version_uri}"
#         logger.warning()
#         return ""
    
def get_annotation_status(value):
    if value == 'mARkdown' or value == 'completed' or value == 'inProgress':
        return value
    else:
        #return 'notYetAnnotated'
        return "(not yet annotated)"

# def ah2ce(date):
#     """convert AH date to CE date"""
#     return 622 + (int(date) * 354 / 365.25)



def get_or_create_country_obj(country_code):
    
    if country_code not in COUNTRY_CODES:
        msg = f"UNKNOWN COUNTRY CODE: {country_code}"
        print(msg)
        logger.warning(msg)
        return None
    else:
        # if the country does not yet exist in the database, create it:
        country_obj = COUNTRY_CODES[country_code]["db_object"]
        if not country_obj:
            # create the country object in the database:
            country_obj, created = Place.objects.get_or_create(
                code=country_code,
                country_code=country_code
            )
            if created:
                IMPORT_STATS["country"] = IMPORT_STATS.get("country", 0) + 1
                if VERBOSE:
                    print("CREATED COUNTRY OBJECT FOR", country_code, country_obj)
            # add the country name in the database:
            country_name = COUNTRY_CODES[country_code]["name"]
            nm = get_or_create_name_obj(country_name, "EN", "country_name")
            link_name_to_obj(nm, place_obj=country_obj, is_preferred=True)

            # store the object for later use:
            COUNTRY_CODES[country_code]["db_object"] = country_obj
    
    return country_obj
    


def get_or_create_place_obj(place_code, part_of_obj):
    """Get a place object from the database, or create it if it does not exist
    
    Args:
        place_code (str): the unique code for a place object
        part_of_obj (obj): generic relation type for hierarchy of places
    """
    pm, created = Place.objects.get_or_create(
        code=place_code
    )
    # if it already existed, return the reference to the object:
    if created:
        IMPORT_STATS["place"] = IMPORT_STATS.get("place", 0) + 1
    else:
        return pm
    
    # check if the place is a known Thurayya URI:
    d = ALTHURAYYA_LOOKUP.get(place_code, None)
    if not d:
        return pm
    
    # get the coordinates and names from the Thurayya dataset
    # and upload them to the database

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
    nm = get_or_create_name_obj(name_ar_prefered, "ar", "toponym")
    link_name_to_obj(nm, place_obj=pm, is_preferred=True)
    
    # add alternative Arabic names:
    for name in re.split(" *، *", d["toponym_arabic_other"]):
        # do not duplicate the prefered name:
        if name == name_ar_prefered:
            continue
        nm = get_or_create_name_obj(name, "ar", "toponym")
        link_name_to_obj(nm, place_obj=pm, is_preferred=False)
    
    # add the preferred Latin name:
    name_lat_prefered = d["toponym_translit"]
    nm = get_or_create_name_obj(name_lat_prefered, "lat", "toponym")
    link_name_to_obj(nm, place_obj=pm, is_preferred=True)
    
    # add alternative Latin names:
    for name in re.split(" *، *", d["toponym_translit_other"]):
        # do not duplicate the prefered name:
        if name == name_lat_prefered:
            continue
        nm = get_or_create_name_obj(name, "lat", "toponym")
        link_name_to_obj(nm, place_obj=pm, is_preferred=False)
    
    # create the region name if it does not exist yet:
    region_code = d["region_code"]
    rm, region_created = Place.objects.get_or_create(
        code=region_code
    )
    if region_created:
        IMPORT_STATS["place"] = IMPORT_STATS.get("place", 0) + 1
        nm = get_or_create_name_obj(d["region_spelled"], "lat", "toponym")
        link_name_to_obj(nm, place_obj=rm, is_preferred=True)
        # Add the normalized Latin region name:
        region_lat = betacodeToSearch(d["region_spelled"])
        nm = get_or_create_name_obj(region_lat, "lat", "toponym")
        link_name_to_obj(nm, place_obj=rm, is_preferred=False)
        

        # Add the Arabic region name:
        reg = re.sub(r"(\W)or ", r"\1أو ", d["region_spelled"])
        region_ar = betacodeToArSimple(reg)
        nm = get_or_create_name_obj(region_ar, "ar", "toponym")
        link_name_to_obj(nm, place_obj=rm, is_preferred=True)

    # link the place to the region:
    link_places(pm, rm, part_of_obj)

    return pm

def get_or_create_name_obj(name, language, name_type):
    """Create name objects for authors and link them to the author object"""
    if not name:
        return
    # generate a normalized version of the name:
    if language.upper() in ("ARA", "AR"):
        normalized_name = normalize_ara_light(name)
    elif language.upper() in ("LAT", "EN"):
        normalized_name = betacodeToSearch(name)
    else:
        normalized_name = name
    
    # create the name object:
    d = dict(
        name=name,
        normalized_name=normalized_name,
        language=language
    )
    if name_type:
        d["name_type"] = name_type
    nm, _created = ObjectName.objects.get_or_create(**d)
    if _created:
        IMPORT_STATS["objectName"] = IMPORT_STATS.get("objectName", 0) + 1
        if VERBOSE:
            print("ObjectName created:", nm)
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
        #defaults={"is_preferred": is_preferred}
    )
    if link_created:
        IMPORT_STATS["objectNameLink"] = IMPORT_STATS.get("objectNameLink", 0) + 1
    # if the link already existed but was not preferred until now, make it preferred:
    if is_preferred and not link.is_preferred:
        link.is_preferred = True
        link.save(update_fields=["is_preferred"])
        #print("prefered name", name_obj, link.is_preferred)
        

def link_book_to_author(text_obj, author_obj, rel_type_obj, authority=""):
    rel, created = A2BRelation.objects.get_or_create(
        person_a=author_obj,
        text_b=text_obj,
        relation_type=rel_type_obj,
        authority=authority
    )
    if created:
        IMPORT_STATS["A2BRelation"] = IMPORT_STATS.get("A2BRelation", 0) + 1
        if VERBOSE:
            print("  -> linked book to author:", text_obj, "<->", author_obj)

def link_manuscript_to_author(ms_obj, record, rel_type_obj, authority=""):
    author_uri = record["author_uri"]
    author_obj, _ = get_or_create_author(author_uri, record)
    rel, created = A2BRelation.objects.get_or_create(
        person_a=author_obj,
        manuscript_b=ms_obj,
        relation_type=rel_type_obj,
        authority=authority
    )
    if created:
        IMPORT_STATS["A2BRelation"] = IMPORT_STATS.get("A2BRelation", 0) + 1

def link_manuscript_to_texts(ms_obj, record, rel_type_obj, authority=""):
    """Link a  manuscript object to text_uris of texts inside it"""
    #for text_uri, page_range in record["text_uris"]:
    for text_uri, page_range in record["parts"].items():
        if text_uri == "NA":
            continue
        #print("RELATED TEXT URI:", text_uri)
        #print("PAGE RANGE:", page_range)
        if page_range:
            page_range = "Page range: " + ",".join(page_range)
        else:
            page_range = ""
        # get or create the text object in the database:
        tm, tm_created = Text.objects.get_or_create(
            text_uri=text_uri,
            defaults={
                "notes": page_range
            }
        )
        if tm_created:
            IMPORT_STATS["text"] = IMPORT_STATS.get("text", 0) + 1

        rel, created = A2BRelation.objects.get_or_create(
            manuscript_a=ms_obj,
            text_b=tm,
            relation_type=rel_type_obj,
            authority=authority
        )
        if created:
            IMPORT_STATS["A2BRelation"] = IMPORT_STATS.get("A2BRelation", 0) + 1

def link_manuscript_to_dates(ms_obj, record, source=""):
    if "dates" not in record:
        return
    # try:
    #     dd, mm, yyyy = date.split("-")
    #     try: 
    #         dd = int(dd)
    #     except:
    #         dd = None
    #     try: 
    #         mm = int(mm)
    #     except:
    #         mm = None
    #     try:
    #         yyyy = int(yyyy)
    #     except:
    #         yyyy = None
    # except:
    #     dd = None
    #     mm = None
    #     yyyy = None
    for date, page_range in record["dates"]:
        year, month, day, precision, modifier = parse_date_str(date)
        date_obj = get_or_create_date(
            date_type_slug="date_written",
            calendar_slug="AH",
            date_str=date,
            year=year,
            month=month,
            day=day,
            precision=precision,
            source="YML",
        )
        if date_obj:
            dlm, created = DateLink.objects.get_or_create(date=date_obj, manuscript=ms_obj)
            if created:
                IMPORT_STATS["dateLink"] = IMPORT_STATS.get("dateLink", 0) + 1



def link_manuscript_to_whole(holding_obj, ms_obj, record, rel_type_obj, authority=""):
    if "ms_part_of" in record:
        parent_uri = record["ms_part_of"]
        print("PARENT URI:", parent_uri)
        parent_obj, created = Manuscript.objects.get_or_create(
            manuscript_uri=parent_uri,
            manuscript_holding=holding_obj
        )
        if created:
            IMPORT_STATS["manuscript"] = IMPORT_STATS.get("manuscript", 0) + 1
        
        rel, created = A2BRelation.objects.get_or_create(
            manuscript_a=ms_obj,
            manuscript_b=parent_obj,
            relation_type=rel_type_obj,
            authority=authority
        )
        if created:
            IMPORT_STATS["A2BRelation"] = IMPORT_STATS.get("A2BRelation", 0) + 1

def link_places(place_a, place_b, rel_type_obj, authority=""):
    if not (place_a and place_b):
        print("None-existent place:")
        print("- place_a:", place_a)
        print("- place_b:", place_b)
        return
    rel, _created = A2BRelation.objects.get_or_create(
        place_a=place_a,
        place_b=place_b,
        relation_type=rel_type_obj,
        authority=authority
    )
    if _created:
        IMPORT_STATS["A2BRelation"] = IMPORT_STATS.get("A2BRelation", 0) + 1
        if VERBOSE:
            print("Created relation between", place_a, "and", place_b)

    return rel



def link_manuscript_to_titles(mm, record):
    """Add various titles to a manuscript object"""
    if type(record['title_ar']) == str:
        record['title_ar'] = record['title_ar'].split(" :: ")
    for name in record['title_ar']:
        nm = get_or_create_name_obj(name, "ar", "title")
        link_name_to_obj(nm, manuscr_obj=mm, is_preferred=False)
    
    if type(record['title_lat']) == str:
        record['title_lat'] = record['title_lat'].split(" :: ")
    for name in record['title_lat']:
        nm = get_or_create_name_obj(name, "lat", "title")
        link_name_to_obj(nm, manuscr_obj=mm, is_preferred=False)
    name = record['title_ar_prefered']
    nm = get_or_create_name_obj(name, "ar", "title")
    link_name_to_obj(nm, manuscr_obj=mm, is_preferred=True)
    name = record['title_lat_prefered']
    nm = get_or_create_name_obj(name, "lat", "title")
    link_name_to_obj(nm, manuscr_obj=mm, is_preferred=True)

def link_book_to_titles(tm, record):
    """Add various titles to a book/text object"""
    # NB: these include titles from metadata header
    if type(record['titles_ar']) == str:
        record['titles_ar'] = re.split(r" *[;,:]+ *", record['titles_ar'])
    for name in record['titles_ar']:
        nm = get_or_create_name_obj(name, "ar", "title")
        link_name_to_obj(nm, text_obj=tm, is_preferred=False)

    if type(record['titles_lat']) == str:
        record['titles_lat'] = re.split(r" *[;,:]+ *", record['titles_lat'])
    for name in record['titles_lat']:
        nm = get_or_create_name_obj(name, "lat", "title")
        link_name_to_obj(nm, text_obj=tm, is_preferred=False)
    
    name = record['title_ar_prefered']
    nm = get_or_create_name_obj(name, "ar", "title")
    link_name_to_obj(nm, text_obj=tm, is_preferred=True)
    name = record['title_lat_prefered']
    nm = get_or_create_name_obj(name, "lat", "title")
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
    if link_created:
        IMPORT_STATS["textTypeLink"] = IMPORT_STATS.get("textTypeLink", 0) + 1
    # if the link already existed but was not preferred until now, make it preferred:
    if is_preferred and not link_created and not link.is_preferred:
        link.is_preferred = True
        link.save(update_fields=["is_preferred"])

def add_holding_names(hm, record):
    """Add various names to a manuscript holding object"""
    if "inst_names" in record:
        for language in record["inst_names"]:
            lang_code = language.lower()[:2]
            for name in record["inst_names"][language]:
                nm = get_or_create_name_obj(name, lang_code, "institution_name")
                link_name_to_obj(nm, loc_obj=hm, is_preferred=False)
    else:
        for name in record['institution_ar'].split(" :: "):
            nm = get_or_create_name_obj(name, "ar", "institution_name")
            link_name_to_obj(nm, loc_obj=hm, is_preferred=False)
        for name in record['institution_lat'].split(" :: "):
            nm = get_or_create_name_obj(name, "lat", "institution_name")
            link_name_to_obj(nm, loc_obj=hm, is_preferred=False)

def add_city_names(city_obj, record):
    """Add various names to a manuscript holding object"""
    if "city_names" in record:
        for language in record["city_names"]:
            lang_code = language.lower()[:2]
            for name in record["city_names"][language]:
                nm = get_or_create_name_obj(name, lang_code, "city_name")
                link_name_to_obj(nm, place_obj=city_obj, is_preferred=False)
    else:
        for name in record['city_ar'].split(" :: "):
            nm = get_or_create_name_obj(name, "ar", "city_name")
            link_name_to_obj(nm, place_obj=city_obj, is_preferred=False)
        for name in record['city_lat'].split(" :: "):
            nm = get_or_create_name_obj(name, "lat", "city_name")
            link_name_to_obj(nm, place_obj=city_obj, is_preferred=False)

def add_author_names(am, record):
    """Add various names to an author object"""
    # first add shuhras, which should be the prefered name: 
    for lang in record["name_elements"]:
        d = record["name_elements"][lang]
        if "shuhra" in d and d["shuhra"]:
                name = d["shuhra"]
                nm = get_or_create_name_obj(name, lang.lower(), "shuhra")
                link_name_to_obj(nm, author_obj=am, is_preferred=True)

    # Then add other name elements, from the record["name_elements"] dictionary
    # (key: language, value: dictionary of name elements)
    #print(json.dumps(record, indent=2, ensure_ascii=False))
    for lang in record["name_elements"]:
        d = record["name_elements"][lang]
        # set one of the following (in this order) as the prefered name:
        pref_els = ["full_name", "nisba"] 
        has_prefered = ObjectNameLink.objects.filter(
            author=am,
            is_preferred=True,
            object_name__language=lang.lower()
        ).exists()
        for name_el in pref_els:
            if name_el in d and d[name_el]:
                name = d[name_el]
                #print("NAME:", name)
                nm = get_or_create_name_obj(name, lang.lower(), name_el.lower())
                if has_prefered:
                    link_name_to_obj(nm, author_obj=am, is_preferred=False)
                else:
                    link_name_to_obj(nm, author_obj=am, is_preferred=True)
                    has_prefered = True
        # add the other name elements, which are by definition not prefered:
        for name_el, name in d.items():
            if name_el not in pref_els:
                nm = get_or_create_name_obj(name, lang.lower(), name_el.lower())
                link_name_to_obj(nm, author_obj=am, is_preferred=False)

    # then add any prefered names that are not yet included:
    for lang in ["ar", "lat"]:
        has_prefered = ObjectNameLink.objects.filter(
            author=am,
            is_preferred=True,
            object_name__language=lang.lower()
        ).exists()
        name = record.get(f'author_{lang}_prefered', "")
        if name:
            nm = get_or_create_name_obj(name, lang, "")
            link_name_to_obj(nm, author_obj=am, is_preferred=not(has_prefered))
        else:
            msg = f'No value for author_{lang}_prefered in record {record}'
            if VERBOSE:
                print(msg)
            logger.warning(msg)
    
    # finally, add the name from the URI:
    name = record['author_from_uri']
    nm = get_or_create_name_obj(name, "lat", "from_uri")
    link_name_to_obj(nm, author_obj=am, is_preferred=False, source="URI")
    
    # for name in record['author_ar'].split(" :: "):
    #     nm = get_or_create_name_obj(name, "ar", "full_name")
    #     #link_author_name(am, nm, is_preferred=False)
    #     link_name_to_obj(nm, author_obj=am, is_preferred=False)
    # for name in record['author_lat'].split(" :: "):
    #     nm = get_or_create_name_obj(name, "lat", "full_name")
    #     #link_author_name(am, nm, is_preferred=False)
    #     link_name_to_obj(nm, author_obj=am, is_preferred=False)
    # for name in record['author_ar_prefered'].split(" :: "):
    #     nm = get_or_create_name_obj(name, "ar", "full_name")
    #     #link_author_name(am, nm, is_preferred=True)
    #     link_name_to_obj(nm, author_obj=am, is_preferred=True)
    # for name in record['author_lat_prefered'].split(" :: "):
    #     nm = get_or_create_name_obj(name, "lat", "full_name")
    #     #link_author_name(am, nm, is_preferred=True)
    #     link_name_to_obj(nm, author_obj=am, is_preferred=True)

def parse_date_str(date_str):
    date_upper = date_str.strip().upper()
    modifier = ""
    date_str = re.sub(r" *\(X+ FOR UNKNOWN\)", "", date_str)
    
    try:
        date_str = re.findall(r"[X\d]+[/-][X\da-zA-Z]+[/-][X\da-zA-Z]+", date_upper)[0]
        if date_str != date_upper:
            if "BEFORE" in date_upper:
                modifier = "before"
            elif "AFTER" in date_upper:
                modifier = "after"
            msg = f"Date contains modifier: '{date_upper}'"
            logger.warning(msg)
            if VERBOSE:
                print(msg)
            
    except Exception as e:
        msg = f"UNKNOWN DATE FORMAT: '{date_upper}'"
        logger.warning(msg)
        print(e, msg)
        #input("CONTINUE")
        return None, None, None, None, None

    # YYYY-MM-DD:
    if re.findall(r"[X\d]{3,4}[/-][X\d]{1,2}[/-][X\d]{1,2}", date_str):
        year, month, day = re.split(r"[/-]", date_str)
    # DD-MM-YYYY
    elif re.findall(r"[X\d]{1,2}[/-][X\d]{2}[/-][X\d]{3,4}", date_str):
        day, month, year = re.split(r"[/-]", date_str)
    
    # YYYY-MMM-DD (Lunar month abbreviation)
    elif re.findall(r"[X\d]{3,4}[/-][a-zA-Z]{2,3}\d?[/-][X\d]{1,2}", date_str):
        year, month_str, day = re.split(r"[/-]", date_str)
        month = LUNAR_MONTHS.get(month_str.upper(), "0")
    # DD-MMM-YYYY (Lunar month abbreviation)
    elif re.findall(r"[X\d]{1,2}[/-][a-zA-Z]{2,3}\d?[/-][X\d]{3,4}", date_str):
        day, month_str, year = re.split(r"[/-]", date_str)
        month = LUNAR_MONTHS.get(month_str.upper(), "0")
    
    # KNOWN YEAR, UNKNOWN DAY AND MONTH:
    # YYYY-XXX?-XX
    elif re.findall(r"\d+[X\d]*[/-]X+[/-]X+", date_str):
        year, month, day = re.split(r"[/-]", date_str)
    # XX-XXX?-YYYY
    elif re.findall(r"X+[/-]X+[/-]\d+[X\d]*", date_str):
        day, month, year = re.split(r"[/-]", date_str)
    # YYYY-MON-DA
    elif re.findall(r"\d+[X\d]*[/-]MON[/-]DA", date_str):
        year, _, _ = re.split(r"[/-]", date_str)
        month = "0"
        day = "0"
    # KNOWN YEAR AND MONTH, UNKNOWN DAY:
    # YYYY-MMM-XX
    elif re.findall(r"\d+[/-][a-zA-Z]{2,3}\d?[/-]DA", date_str):
        year, month_str, day = re.split(r"[/-]", date_str)
        month = LUNAR_MONTHS.get(month_str.upper(), "0")
        day = "0"
    else:
        msg = f"UNKNOWN DATE FORMAT: '{date_str}'"
        logger.warning(msg)
        if VERBOSE:
            print(msg)
        return None, None, None, None, None
    
    # convert date elements to integers:
    precision = "day" # default; will be reset if not all date elements are fully present
    try:
        year = int(year)
    except:
        if re.findall(r"\dXXX\b", year):
            precision = "millennium"
        elif re.findall(r"\dXX\b", year):
            precision = "century"
        elif re.findall(r"\dX\b", year):
            precision = "decade"
        try:
            year = int(year.replace("X", "0"))
        except:
            year = None
    try:
        month = int(month)
    except:
        month = 0
    try:
        day = int(day)
    except:
        day = 0
    
    # define the level of precision of the date:
    if day == 0:
        day = None
        precision = "month"
    if month == 0:
        month = None
        precision = "year"

    return year, month, day, precision, modifier


def add_author_dates(am, record):
    # add dates related to the author:
    # first, create the date itself:
    date_str = record["date_str"]
    date_obj = get_or_create_date(
        date_type_slug="death_date",
        calendar_slug="AH",
        date_str=date_str,
        year=int(date_str),
        precision="year",
        source="URI",
    )
    # then, add the link to the author:
    if date_obj:
        dlm, created = DateLink.objects.get_or_create(date=date_obj, author=am)
        if created:
            IMPORT_STATS["dateLink"] = IMPORT_STATS.get("dateLink", 0) + 1
    
    # process death and birth dates from yml file:
    for date_type_slug, dates_d in record["dates"].items():
        for cal, cal_dates in dates_d.items():
            print(cal_dates)
            if type(cal_dates) == list:
                cal_dates = re.split(r" *(?:\bOR\b|\bor\b|[;:,])+ *", ",".join(cal_dates)) 
            elif type(cal_dates) == str:
                cal_dates = re.split(r" *(?:\bOR\b|\bor\b|[;:,])+ *", cal_dates.strip())
            for date_str in cal_dates:
                
                year, month, day, precision, modifier = parse_date_str(date_str)
                print(f"-> {date_str} => year {year}, month {month}, day {day}")
                # TODO: deal with modifiers like "before" and "after"
                if not year:
                    continue

                date_obj = get_or_create_date(
                    date_type_slug=date_type_slug,
                    calendar_slug=cal,
                    date_str=date_str,
                    year=year,
                    month=month,
                    day=day,
                    precision=precision,
                    source="YML",
                )

                if date_obj:
                    dlm, created = DateLink.objects.get_or_create(date=date_obj, author=am)
                    if created:
                        IMPORT_STATS["dateLink"] = IMPORT_STATS.get("dateLink", 0) + 1
            


    
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
        if created:
            IMPORT_STATS["dateType"] = IMPORT_STATS.get("dateType", 0) + 1
            DATE_TYPES[date_type_slug] = dt
    try:
        cal = CALENDARS[calendar_slug]
    except:
        cal, created = Calendar.objects.get_or_create(
            slug=calendar_slug,
            name=calendar_slug
        )
        if created:
            IMPORT_STATS["calendar"] = IMPORT_STATS.get("calendar", 0) + 1
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
        if _created:
            IMPORT_STATS["date"] = IMPORT_STATS.get("date", 0) + 1
    except Exception as e: 
        msg = f"CREATING DATE OBJECT FAILED: {e}"
        print(msg)
        debug_dict = dict(
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
            )
        print(traceback.format_exc())
        print(debug_dict)
        logger.warning(msg)
        logger.warning("%s" % debug_dict)
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
            msg = f"NO WORLDCAT ID FOUND in {link}"
            print(msg)
            logger.warning(msg)
            #input("CONTINUE?")
            return
        
        # create the external ID
        id_obj, created = ExternalID.objects.get_or_create(
            provider=worldcat_obj,
            external_id=worldcat_id
        )
        if created:
            IMPORT_STATS["externalID"] = IMPORT_STATS.get("externalID", 0) + 1

        # link the edition to the external ID:
        rel, created = ExternalIDLink.objects.get_or_create(
            identifier=id_obj,
            edition=edition_obj
        )
        if created:
            IMPORT_STATS["externalIDLink"] = IMPORT_STATS.get("externalIDLink", 0) + 1



def attach_dates_to_author(author, date_objs):
    """
    Bulk-create DateLink rows (safe with through model).
    """
    links = [DateLink(date=d, author=author) for d in date_objs]
    DateLink.objects.bulk_create(links, ignore_conflicts=True)

# def split_tag_list(tag_list):
#     version_tags = []
#     text_tags = []
#     author_tags = []
 
#     for tag in tag_list:
#         if "MARKDOWN" in tag:
#             version_tags.append("MARKDOWN")
#         elif "COMPLETED" in tag:
#             version_tags.append("COMPLETED")
#         elif "INPROGRESS" in tag:
#             version_tags.append("INPROGRESS")
#         elif "CLEANED_VERSION" in tag:
#             version_tags.append("CLEANED_VERSION")
#         elif "NO_MAJOR_ISSUES" in tag:
#             version_tags.append("NO_MAJOR_ISSUES")
#         #elif "born@" in tag or "died@" in tag or "resided@" in tag or "visited@" in tag:
#         elif re.findall("born@|died@|resided@|visited@", tag):
#             author_tags.append(tag)
#         elif "@" in tag or tag.startswith("_"):
#             text_tags.append(tag)
#         else:
#             version_tags.append(tag)
#     return version_tags, text_tags, author_tags

def clean(s):
    s = re.sub(" *¶ *", " ", s)
    return s.strip()
        
# def format_fields(data, base_url):
#     record = dict()
    
#     record['version_uri'] = data['versionUri']


#     # TODO: deal with multi-language items!
#     if "language" in data:
#         record['version_lang'] = data['language']
#     else:
#         record['version_lang'] = get_version_lang(record['version_uri'])
    
#     if data['date']:
#         date = int(data['date'])
#     else:
#         date = None
#     record['date'] = date
#     record['date_AH'] = date
#     record['date_CE'] = None
#     record['date_str'] = date
#     # add normalized versions + prefered version of the arabic-script author name:
#     author_ar = re.split(' *:: *| *, *| *; *', clean(data['author_ar']))
#     #normalized_author_ar = [normalize_ara_light(clean(a)) for a in author_ar if a]
#     #record['author_ar'] = " :: ".join(list(set(author_ar + normalized_author_ar)))
#     record['author_ar'] = " :: ".join(list(set(author_ar)))
#     record['author_ar_prefered'] = author_ar[0]
#     # add normalized versions + prefered version of the latin-script author name:
#     author_lat_shuhra = re.split(' *:: *| *, *| *; *', clean(data['author_lat_shuhra']))
#     author_lat = re.split(' *:: *| *, *| *; *', clean(data['author_lat']))
#     if data['author_lat_shuhra']:
#         record['author_lat_prefered'] = author_lat_shuhra[0]
#     else:
#         record['author_lat_prefered'] = author_lat[0]
#     author_lat += author_lat_shuhra
#     #normalized_author_lat = [betacodeToSearch(a) for a in author_lat if a]
#     #record['author_lat'] = " :: ".join(list(set(author_lat + normalized_author_lat)))
#     record['author_lat'] = " :: ".join(list(set(author_lat)))

#     record['text_uri'] = data['book']
#     record['author_uri'] = data['book'].split(".")[0]

#     # add normalized version of the Arabic-script titles:
#     titles_ar = re.split(' *:: *| *, *| *; *', clean(data['title_ar']))
#     #normalized_titles_ar = [normalize_ara_light(clean(t)) for t in titles_ar if t]
#     #record['titles_ar'] = " :: ".join(list(set(titles_ar + normalized_titles_ar)))
#     record['titles_ar'] = " :: ".join(list(set(titles_ar)))
#     # add normalized version of the Latin-script titles:
#     titles_lat = re.split(' *:: *| *, *| *; *', clean(data['title_lat']))
#     #normalized_titles_lat = [betacodeToSearch(t) for t in titles_lat if t]
#     #record['titles_lat'] = " :: ".join(list(set(titles_lat + normalized_titles_lat)))
#     record['titles_lat'] = " :: ".join(list(set(titles_lat)))

#     # define the preferred title: 
#     record['title_ar_prefered'] = titles_ar[0]
#     record['title_lat_prefered'] = titles_lat[0]

#     record['ed_info'] = clean(data['ed_info'])
#     if "worldcat.org" in record['ed_info']:
#         ed_info = []
#         worldcat_links = []
#         for el in record['ed_info'].split(" :: "):
#             if "worldcat.org" in el:
#                 worldcat_links.append(el)
#             elif el.strip():
#                 ed_info.append(el)
#         record['ed_info'] = " :: ".join(ed_info)
#         record["worldcat_links"] = worldcat_links
#     record['version_code'] = data['id']

#     # check if the version is part of a text file that was split because of its size:
#     if re.findall("[A-Z]$", data['id']):
#         record["part_of"] = data['id'][:-1]
#         print(data['id'], "is part of", data['id'][:-1])

#     try:
#         record["collection_code"] = re.findall(r"^([A-Za-z]+?\d*[A-Za-z]+)\d+(?:BK\d+)?(?:Vols)?[A-Z]?$", data['id'])[0]
#     except:
#         record["collection_code"] = None
#         print("Collection code not found in", data['id'])
#     version_tags, text_tags, author_tags = split_tag_list(data['tags'].split(" :: "))
#     record["version_tags"] = " :: ".join([t for t in version_tags if t])
#     record["text_tags"] = " :: ".join([t for t in text_tags if t])
#     record["author_tags"] = " :: ".join([t for t in author_tags if t])
    

#     record['author_from_uri'] = data['author_from_uri']
#     record['author_lat_shuhra'] = data['author_lat_shuhra']
#     record['author_lat_full_name'] = clean(data['author_lat_full_name'])

#     ##releasefields
#     record['char_length'] = data['char_length']
#     record['tok_length'] = data['tok_length']
#     # record['url'] = data['url'].replace("../data", base_url)  # this creates problems with v2022.2.7, which has ../data/xxxxAH/data/
#     record['url'] = re.sub( ".{,15}/data", base_url, data['url'])   # greedy quantifier `{,}` deals with both situations: ../data/ and ../data/xxxxAH/data/
#     record['analysis_priority'] = data['status']
#     record['annotation_status'] = get_annotation_status(data['url'].split('.')[-1])
#     if "type" in data:
#         record["type"] = data["type"]
#     else:
#         record["type"] = "book"

#     ##manuscriptfields:
#     ms_keys = ['city_ar', 'city_lat', 'institution_ar', 'institution_lat', 
#                'catalog_ref', 'shelfmark']
#     for k in ms_keys:
#         if k in data:
#             record[k] = data[k]
#         else:
#             record[k] = ""
    
#     manuscript_uri = ".".join(data["versionUri"].split(".")[:2])
#     record["manuscript_uri"] = manuscript_uri

#     if "uncorrected_OCR" in data:
#         if data["uncorrected_OCR"] in ("FALSE", "False", False):
#            record["uncorrected_OCR"] = False
#         elif data["uncorrected_OCR"] in ("TRUE", "True", True):
#            record["uncorrected_OCR"] = True
#         else:
#             print("Unexpected value for 'uncorrected_OCR':", repr(data["uncorrected_OCR"]))
#             record["uncorrected_OCR"] = None
#     else:
#         if "UNCORRECTED_OCR" in data["tags"]:
#             record["uncorrected_OCR"] = True
#         else:
#             record["uncorrected_OCR"] = None            

#     if "subcorpus" in data:
#         record["subcorpus"] = data["subcorpus"].lower()
#     else:
#         record["subcorpus"] = record['version_lang'].lower()

#     # deal with manuscripts that contain one or more specific texts:
#     record["text_uris"] = []
#     if "parts" in data:
#         for part in re.split(" *[;,:]+ *", data["parts"]):
#             if not part:
#                 continue
#             if "@" in part:
#                 text_uri, page_range = part.split("@")
#                 record["text_uris"].append((text_uri, page_range))
#             else:
#                 record["text_uris"].append((part, None))

#     # check if the manuscript object is part of a complete manuscript:
#     if re.findall(r"P\d+[AB]?\d*$", manuscript_uri):
#         parent = re.sub(r"P\d+[AB]?\d*$", "", manuscript_uri)
#         record["ms_part_of"] = parent
#         print(manuscript_uri, "is part of", parent)
    
#     return record

def get_or_create_book(text_uri, authorship_obj=None, book_type_obj=None, 
                       book_record=dict(), am=None, part_of_obj=None):
    # CHECK WHETHER THE TEXT_URI REALLY IS A URI?
    #if not re.findall(r"\d{4}[A-Za-z]+\.[A-Za-z]+\w+", text_uri):
    #    return
    try:
        tm = Text.objects.get(
            text_uri=text_uri
        )
        tm_created = False
        if VERBOSE:
            print("Text already in the database:", text_uri)
    except: 
        # the text is not yet in the database! Create a new text object:
        if VERBOSE:
            print("Text not yet in database:", text_uri)
        tm, tm_created = Text.objects.update_or_create(
            text_uri=text_uri,
            #author=am,  # we add the author(s) with link_book_to_author
            defaults=dict(
                tags=book_record.get("tags", ""),
                bibliography=book_record.get("bibliography", ""),
                notes=book_record.get("notes", ""),
            )
        )
        if tm_created:
            IMPORT_STATS["text"] = IMPORT_STATS.get("text", 0) + 1
            if VERBOSE:
                print("-> created", text_uri)
    
    if am and authorship_obj:
        link_book_to_author(tm, am, authorship_obj, authority="URI")
    if book_type_obj:
        add_book_type(tm, book_type_obj, source="URI")
    if book_record:
        link_book_to_titles(tm, book_record)
    
        # add external IDs:
        for provider, id_list in book_record["external_ids"].items():
            prov_obj = None
            for ext_id in id_list:
                prov_obj, _, _ = add_external_id(provider, ext_id, 
                                                prov_obj=prov_obj, text=tm)

        # Add related places:
        add_related(tm, text_uri, book_record["place_relations"], 
                    part_of_obj, authority="OpenITI metadata")
        # Add related texts:
        add_related(tm, text_uri, book_record["text_relations"], 
                    part_of_obj, authority="OpenITI metadata")
        # Add related persons:
        add_related(tm, text_uri, book_record["person_relations"], 
                    part_of_obj, authority="OpenITI metadata")
        
    
    return tm, tm_created

def add_related(source_obj, source_uri, related_list, 
                part_of_obj, authority=""):
    for d in related_list:
        try:
            key_a = [k for k in d if k.endswith("_a")][0]
            key_b = [k for k in d if k.endswith("_b")][0]
        except:
            msg = f"_a or _b key not found in dict: {d}" 
            if VERBOSE:
                print(msg)
            logger.warning(msg)
            continue

        if d[key_a] == source_uri:
            obj_a = source_obj
            # get or create the target object:
            if key_b == "place_b":
                obj_b = get_or_create_place_obj(d["place_b"], part_of_obj)
            elif key_b == "text_b":
                obj_b, _  = get_or_create_book(d["text_b"])
            elif key_b == "person_b":
                obj_b, _ = get_or_create_author(d["person_b"])
        elif d[key_b] == source_uri:
            obj_b = source_obj
            # get or create the target object:
            if key_a == "place_a":
                obj_a = get_or_create_place_obj(d["place_a"], part_of_obj)
            elif key_a == "text_a":
                obj_a, _  = get_or_create_book(d["text_a"])
            elif key_a == "person_a":
                obj_a, _ = get_or_create_author(d["person_a"])
        else:
            print("Neither _a or _b key is the source_uri!")
            print("Source uri:", source_uri)
            print("dict:", d)
        
        # get or create relationship type object:
        rel_type_obj, created = RelationType.objects.get_or_create(
            code=d["code"],
            subtype_code=d["subtype_code"]
        )
        if created:
            IMPORT_STATS["relationType"] = IMPORT_STATS.get("relationType", 0) + 1
        
        # link the two entities:
        rel, created = A2BRelation.objects.get_or_create(**{
            key_a: obj_a,
            key_b: obj_b,
            "relation_type":rel_type_obj,
            "authority":authority
        })
        if created:
            IMPORT_STATS["A2BRelation"] = IMPORT_STATS.get("A2BRelation", 0) + 1
            
        

# def add_related(source_obj, source_obj_type, related_list, 
#                 part_of_obj, authority=""):
#     if not related_list:
#         return
#     # first, assign the source object to the correct variable:
#     if source_obj_type.endswith("_a"):
#         person_a = None
#         text_a = None
#         edition_a = None
#         place_a = None
#         manuscript_a = None
#         if source_obj_type == "person_a":
#             person_a = source_obj
#         elif source_obj_type == "text_a":
#             text_a = source_obj
#         elif source_obj_type == "place_a":
#             place_a = source_obj
#     else:
#         person_b=None
#         text_b=None
#         edition_b=None
#         place_b=None
#         manuscript_b=None
#         if source_obj_type == "person_b":
#             person_b = source_obj
#         elif source_obj_type == "text_b":
#             text_b = source_obj
#         elif source_obj_type == "place_b":
#             place_b = source_obj

#     for d in related_list:
#         if source_obj_type.endswith("_a"):
#             person_b=None
#             text_b=None
#             edition_b=None
#             place_b=None
#             manuscript_b=None
#             # first, get or create the target object:
#             if "place_b" in d:
#                 place_b = get_or_create_place_obj(d["place_b"], part_of_obj)
#             elif "text_b" in d:
#                 # TODO: add a check that this is a real book URI!?
#                 text_b  = get_or_create_book(d["text_b"])
#             elif "person_b" in d:
#                 person_b = get_or_create_author(d["person_b"])
#         else:
#             person_a=None
#             text_a=None
#             edition_a=None
#             place_a=None
#             manuscript_a=None
#             # first, get or create the target object:
#             if "place_a" in d:
#                 place_a = get_or_create_place_obj(d["place_a"], part_of_obj)
#             elif "text_a" in d:
#                 # TODO: add a check that this is a real book URI!?
#                 text_a  = get_or_create_book(d["text_a"])
#             elif "person_a" in d:
#                 person_a = get_or_create_author(d["person_a"])
        
#         # get or create relationship type object:
#         rel_type_obj, created = RelationType.objects.get_or_create(
#             code=d["code"],
#             subtype_code=d["subtype_code"]
#         )
        
#         # link the two entities:
#         rel, created = A2BRelation.objects.get_or_create(
#             person_a=person_a,
#             person_b=person_b,
#             text_a=text_a,
#             text_b=text_b,
#             place_a=place_a,
#             place_b=place_b,
#             edition_a=edition_a,
#             edition_b=edition_b,
#             manuscript_a=manuscript_a,
#             manuscript_b=manuscript_b,
#             relation_type=rel_type_obj,
#             authority=authority
#         )
        
        



def add_external_id(provider,ext_id, prov_obj=None, author=None, text=None,
                    manuscript=None, manuscript_holding=None,
                    place=None, edition=None, version=None):
    if not prov_obj:
        slug = re.sub(r"\W+", "", provider.lower())
        prov_obj, created = IdentifierProvider.objects.get_or_create(
            slug=slug
        )
        if created:
            IMPORT_STATS["IdentifierProvider"] = IMPORT_STATS.get("IdentifierProvider", 0) + 1
    
    id_obj, created = ExternalID.objects.get_or_create(
        provider=prov_obj,
        external_id=ext_id
    )
    if created:
        IMPORT_STATS["externalID"] = IMPORT_STATS.get("externalID", 0) + 1
    
    link_obj, created = ExternalIDLink.objects.get_or_create(
        identifier=id_obj,
        author=author,
        text=text,
        manuscript=manuscript,
        manuscript_holding=manuscript_holding,
        place=place,
        edition=edition,
        version=version
    )
    if created:
        IMPORT_STATS["externalIDLink"] = IMPORT_STATS.get("externalIDLink", 0) + 1
    return prov_obj, id_obj, link_obj


def get_or_create_version(record, release_obj, worldcat_obj, tm=None, mm=None):
    vm = None
    vm_created = None
    # now we are sure the author and text exist in the database, create a new version object:

    # (but first, we check if the edition meta object exists or create it)
    
    header_meta = record.get("header_meta", {})
    ed_info = header_meta.get("Edition:Editor", []) + \
              header_meta.get("Edition:Place", []) + \
              header_meta.get("Edition:Date", []) + \
              header_meta.get("Edition:Publisher", [])
    try:
        em = Edition.objects.filter(
            text=tm,
            manuscript=mm,
            ed_info=" :: ".join(ed_info)
        )[0]  # more than one edition with the same query criteria may exist!; 
        # NB: .first() returns None if none exists, so it will not trigger the exception
        # if VERBOSE:
        #     print("Edition does exist")
        #     print("em:", em)
        #     print()
    except: 
        if VERBOSE:
            print("The edition is not yet in the database")

        if ed_info:
            if tm:
                em, em_created = Edition.objects.update_or_create(
                    text=tm,
                    ed_info=" :: ".join(ed_info),
                    defaults=dict(
                        editor = " :: ".join(header_meta.get("Edition:Editor", [])),
                        edition_place = " :: ".join(header_meta.get("Edition:Place", [])),
                        publisher = " :: ".join(header_meta.get("Edition:Publisher", [])),
                        pdf_url=record["pdf_url"],
                    )
                )
            else:
                em, em_created = Edition.objects.update_or_create(
                    manuscript=mm,
                    ed_info=" :: ".join(ed_info),
                    defaults=dict(
                        editor = " :: ".join(header_meta.get("Edition:Editor", [])),
                        edition_place = " :: ".join(header_meta.get("Edition:Place", [])),
                        publisher = " :: ".join(header_meta.get("Edition:Publisher", [])),
                        pdf_url=record["pdf_url"],
                    )
                )

            if em_created:
                IMPORT_STATS["edition"] = IMPORT_STATS.get("edition", 0) + 1
                if VERBOSE:
                    print("-> Created Edition object", em)

            # add the edition date(s):
            dates = header_meta.get("Edition:Date", [])
            for date in dates:
                if len(re.findall(r"\d+", date)) == 1:
                    date_str = re.findall(r"\d+", date)[0]
                    date_int = int(date_str)
                    if date_int > 1450:
                        calendar = "CE"
                    else:
                        calendar = "AH"
                    date_obj = get_or_create_date("published", calendar, date_str,
                        year=date_int, precision="year", source="text header")
                    if date_obj:
                        dlm, created = DateLink.objects.get_or_create(date=date_obj, edition=em)
                        if created:
                            IMPORT_STATS["dateLink"] = IMPORT_STATS.get("dateLink", 0) + 1

            # add worldcat link to external_ids:
            add_worldcat_id(em, record, worldcat_obj)
            
        else:
            em = None
            em_created = False

    # upload the collection code if it doesn't exist yet:
    cm, cm_created = SourceCollectionDetails.objects.get_or_create(
        code=record["collection_code"]
    )
    if cm_created:
        IMPORT_STATS["sourceCollection"] = IMPORT_STATS.get("sourceCollection", 0) + 1

    # now create the new version object:

    if "part_of" in record and record["part_of"]:
        whole_obj = Version.objects.get(version_uri=record["part_of"])
    else:
        whole_obj = None
    try:
        vm, vm_created = Version.objects.update_or_create(
            version_code=record["version_code"],
            version_uri=record["version_uri"],
            text=tm,
            manuscript=mm,
            language=record["language"],
            defaults=dict(
                edition=em,
                source_coll=cm,
                part_of=whole_obj
            )
        )
    except Exception as e:
        msg = f"ERROR {e} while creating version record for {record['version_uri']}"
        logger.warning(msg)
        print(msg)
        return None, None
    if vm_created:
        IMPORT_STATS["version"] = IMPORT_STATS.get("version", 0) + 1
        if VERBOSE:
            print("-> created version:", record['version_uri'])
        # add language_script_combo field
        add_version_language(vm, record)

    # add external IDs:
    for provider, id_list in record["external_ids"].items():
        prov_obj = None
        for ext_id in id_list:
            prov_obj, _, _ = add_external_id(provider, ext_id, 
                                                prov_obj=prov_obj, version=vm)
    


    
    # now that we know that the version object is in the database, 
    # create or update the ReleaseVersion object:
    rvm, rvm_created = ReleaseVersion.objects.update_or_create(
        release_info=release_obj,
        version=vm,
        defaults=dict(
            url=record["url"],
            subcorpus=record["subcorpus"],
            uncorrected_ocr=record["uncorrected_OCR"],
            char_length=record["char_length"],
            tok_length=record["tok_length"],
            analysis_priority=record["analysis_priority"],
            annotation_status=record["annotation_status"],
            tags=record["tags"]
        )
    )
    if rvm_created:
        IMPORT_STATS["releaseVersion"] = IMPORT_STATS.get("releaseVersion", 0) + 1
        if VERBOSE:
            print("NEW RELEASE VERSION OBJECT CREATED:", rvm)
    return vm, vm_created

def add_version_language(vm, record):
    for lang_code in record["language"].split(","):
        lm, created = LanguageScriptCombo.objects.get_or_create(
            code=lang_code
        )
        if created:
            msg = "UNKNOWN LANGUAGE CODE: {lang_code}"
            print(msg)
            logger.warning(msg)
        vm.language_script_combo.add(lm)
    #if "," in record["language"]:
    #    print("multiple languages:", vm.language_script_combo.all())
    #    #input("CONTINUE?")

def get_or_create_author(author_uri, record=dict(), part_of_obj=None):  
    try:
        am = Author.objects.get(
            author_uri=author_uri
        )
        am_created = False
        if VERBOSE:
            print("Author already in the database:", author_uri)
    except:
        if VERBOSE:
            print("Author not yet in the database:", author_uri)

        # the author is not yet in the database! Create a new author object:

        am, am_created = Author.objects.get_or_create(
            author_uri=author_uri,
            defaults=dict(
                tags=record.get('author_tags', ""),
                notes=record.get('notes', ""),
                bibliography=record.get('bibliography', ""),
                #external_ids=record.get('external_ids', "")
            )
        )
        if am_created:
            IMPORT_STATS["author"] = IMPORT_STATS.get("author", 0) + 1
            if VERBOSE:
                print("-> created", author_uri)
    
    

    if record:
        # Add names to the author object:
        add_author_names(am, record)
        add_author_dates(am, record)
        
        # Add external IDs
        for provider, id_list in record["external_ids"].items():
            prov_obj = None
            for ext_id in id_list:
                prov_obj, _, _ = add_external_id(provider, ext_id, 
                                                 prov_obj=prov_obj, author=am)

        # Add related places:
        add_related(am, author_uri, record["place_relations"], 
                    part_of_obj, authority="OpenITI metadata")
        # Add related persons:
        add_related(am, author_uri, record["person_relations"], 
                    part_of_obj, authority="OpenITI metadata")

    return am, am_created

def upload_book_corpus_meta(author_d, authorship_obj, release_obj, part_of_obj, 
                            book_type_obj, worldcat_obj, base_url, release_code):
    author_record = collect_author_yml_data(author_d)
    author_uri = author_record["author_uri"]
    print(release_code, author_uri)

    am, am_created = get_or_create_author(author_uri, author_record, part_of_obj)
    # insights["n_authors"] = insights.get("n_authors", 0) + 1
    # if am_created:
    #     insights["n_new_authors"] = insights.get("n_new_authors", 0) + 1
    for book_d in author_d["books"]:
        book_record = collect_text_yml_data(book_d)
        text_uri = book_record["text_uri"]
        tm, tm_created = get_or_create_book(text_uri, authorship_obj, book_type_obj, 
                                book_record, am, part_of_obj)
        # insights["n_books"] = insights.get("n_books", 0) + 1
        # if tm_created:
        #     insights["n_new_books"] = insights.get("n_new_books", 0) + 1
        for version_d in book_d["versions"]:
            version_record = collect_version_yml_data(version_d, base_url)
            version_uri = version_record["version_uri"]
            vm, vm_created = get_or_create_version(version_record, release_obj, 
                                           worldcat_obj, tm=tm)
            # insights["n_versions"] = insights.get("n_versions", 0) + 1
            # if vm_created:
            #     insights["n_new_versions"] = insights.get("n_new_versions", 0) + 1

def upload_ms_corpus_meta(loc_d, authorship_obj, release_obj, part_of_obj, 
                          worldcat_obj, base_url, release_code):
    # check if the version uri is already in the database:
    #print(record)
    loc_record =  collect_loc_yml_data(loc_d)
    loc_uri = loc_record["loc_uri"]
    print(release_code, loc_uri)
    hm = get_or_create_ms_holding(loc_uri, loc_record, part_of_obj)
    for ms_d in loc_d["manuscripts"]:
        ms_record = collect_manuscr_yml_data(ms_d)
        ms_uri = ms_record["manuscript_uri"]
        mm = get_or_create_manuscript(ms_uri, ms_record, authorship_obj, 
                                      hm, part_of_obj)
        for transcr_d in ms_d["transcriptions"]:
            transcr_record = collect_transcr_yml_data(transcr_d, base_url)
            transcr_uri = transcr_record["version_uri"]
            vm, vm_created = get_or_create_version(transcr_record, release_obj, 
                                           worldcat_obj, mm=mm)

def get_or_create_ms_holding(loc_uri, record, part_of_obj):
    hm, hm_created = ManuscriptHolding.objects.get_or_create(
        loc_uri=loc_uri
    )
    if hm_created:
        IMPORT_STATS["manuscriptHolding"] = IMPORT_STATS.get("manuscriptHolding", 0) + 1
        if VERBOSE:
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
        #print(place_code, city_obj)
    else:
        city_obj = None
    
    # Add country to the ManuscriptHolding object:
    country_code = loc_uri[2:6]
    country_obj = get_or_create_country_obj(country_code)
    if country_obj:
        hm.country = country_obj
        #hm.save(update_fields=["city", "country"])

        # link the city to the country:
        if city_obj and country_obj:
            link_places(city_obj, country_obj, part_of_obj)
        #print(country_code, country_obj) 

    # add catalog and links data:
    if "catalogs" in record and record["catalogs"]:
        if not hm.catalogs:
            hm.catalogs = record["catalogs"]
        else:
            catalogs = re.split(" :: ", hm.catalogs)
            for cat in re.split(" *[:;]+ *", record["catalogs"]):
                if cat not in catalogs:
                    catalogs.append(cat)
            hm.catalogs = " :: ".join(catalogs)
    if "links" in record and record["links"]:
        if not hm.links:
            hm.links = record["links"]
        else:
            links = re.split(" :: ", hm.links)
            for link in re.split(" *[:;]+ *", record["links"]):
                if link not in links:
                    links.append(link)
            hm.links = " :: ".join(links)

    # save the updates to the record:
    hm.save(update_fields=["city", "country", "catalogs", "links"])

    return hm

def get_or_create_manuscript(ms_uri, record, authorship_obj, 
                            hm, part_of_obj):
        
        
    mm, mm_created = Manuscript.objects.update_or_create(
        manuscript_uri=ms_uri,
        defaults=dict(
            tags=record["tags"],
            shelfmark=record["shelfmark"],
            manuscript_holding=hm
        )
    )
    if mm_created:
        IMPORT_STATS["manuscript"] = IMPORT_STATS.get("manuscript", 0) + 1
        if VERBOSE:
            print("-> created", record['manuscript_uri'])
    
    link_manuscript_to_titles(mm, record)
    #link_manuscript_to_author(mm, record, authorship_obj)
    link_manuscript_to_texts(mm, record, part_of_obj)
    link_manuscript_to_dates(mm, record)
    link_manuscript_to_whole(hm, mm, record, part_of_obj)

    return mm

    
# def get_or_create_transcr(transcr_uri, record, mm, release_obj, worldcat_obj):
#     try:
#         vm = Version.objects.get(
#             version_uri=transcr_uri
#         )
#     except Version.DoesNotExist:
#         if VERBOSE:
#             print(transcr_uri, "does not exist in the database")

#         header_meta = record.get("header_meta", {})
#         ed_info = header_meta.get("Edition:Editor", []) + \
#                   header_meta.get("Edition:Place", []) + \
#                   header_meta.get("Edition:Date", []) + \
#                   header_meta.get("Edition:Publisher", [])
#         try:
#             em = Edition.objects.filter(
#                 manuscript=mm,
#                 ed_info=" :: ".join(ed_info)
#             )[0]  # more than one edition with the same query criteria may exist!; 
#             # NB: .first() returns None if none exists, so it will not trigger the exception
#             if VERBOSE:
#                 print("Edition does exist")
#                 print("em:", em)
#                 print()
#         except: 
#             if VERBOSE:
#                 print("Neither does the edition exist")

#             em, em_created = Edition.objects.update_or_create(
#                 manuscript=mm,
#                 ed_info=" :: ".join(ed_info),
#                 defaults=dict(
#                     editor = " :: ".join(header_meta.get("Edition:Editor", [])),
#                     edition_place = " :: ".join(header_meta.get("Edition:Place", [])),
#                     publisher = " :: ".join(header_meta.get("Edition:Publisher", [])),
#                     pdf_url=record["links"],
#                 )
#             )
#             # add the edition date(s):
#             dates = header_meta.get("Edition:Date", [])
#             for date in dates:
#                 if len(re.findall(r"\d+", date)) == 1:
#                     date_str = re.findall(r"\d+", date)[0]
#                     date_int = int(date_str)
#                     if date_int > 1450:
#                         calendar = "CE"
#                     else:
#                         calendar = "AH"
#                     date_obj = get_or_create_date("published", calendar, date_str,
#                         year=date_int, precision="year", source="text header")
#                     if date_obj:
#                         DateLink.objects.get_or_create(date=date_obj, edition=em)

#             # add worldcat link to external_ids:
#             add_worldcat_id(em, record, worldcat_obj)

#             if em_created and VERBOSE:
#                 print("-> Created Edition object")

#         # upload the collection code if it doesn't exist yet:
#         cm, cm_created = SourceCollectionDetails.objects.get_or_create(
#             code=record["collection_code"]
#         )

#         # now create the new version object:

#         vm, vm_created = Version.objects.update_or_create(
#             version_code=record["version_code"],
#             version_uri=record["version_uri"],
#             manuscript=mm,
#             language=record["language"], # TODO switch to language-script combo
#             defaults=dict(
#                 #edition=em,  # TODO
#                 source_coll=cm,
#             )
#         ) 

#         # add external IDs:
#         for provider, id_list in record["external_ids"].items():
#             prov_obj = None
#             for ext_id in id_list:
#                 prov_obj, _, _ = add_external_id(provider, ext_id, 
#                                                  prov_obj=prov_obj, version=vm)
#         # TODO: language_script_combo field
        
#         if vm_created and VERBOSE:
#             print("-> created", transcr_uri)              


#     # now that we know that the version object is in the database, 
#     # create or update the ReleaseVersion object:
#     rvm, rvm_created = ReleaseVersion.objects.update_or_create(
#         release_info=release_obj,
#         version=vm,
#         defaults=dict(
#             url=record["url"],
#             subcorpus=record["subcorpus"],
#             uncorrected_ocr=record["uncorrected_OCR"],
#             char_length=record["char_length"],
#             tok_length=record["tok_length"],
#             analysis_priority=record["analysis_priority"],
#             annotation_status=record["annotation_status"],
#             tags=record["tags"]
#         )
#     )
#     if rvm_created and VERBOSE:
#         print("NEW RELEASE VERSION OBJECT CREATED:", rvm)    

def upload_release_meta(meta_fp, base_url, release_info, 
        authorship_obj, book_type_obj, part_of_obj, worldcat_obj,
        meta_upload=True, test=False):
    print(f"Uploading release {release_info['release_code']} metadata...")

    # first, create the new release itself in the database:
    release_obj, created = ReleaseInfo.objects.update_or_create(
        release_code=release_info["release_code"],
        defaults=dict(
            release_date=release_info["release_date"],
            zenodo_link=release_info["zenodo_link"],
            release_notes=release_info["release_notes"]
        )
    )
    if created:
        IMPORT_STATS["releaseInfo"] = IMPORT_STATS.get("releaseInfo", 0) + 1
        if VERBOSE:
            print("NEW RELEASE ENTRY CREATED:", release_obj)
    
    version_codes_d = dict()
    
    with open(meta_fp, 'r', encoding='utf-8') as f:
        data = f.read()
        data = re.sub(r" *¶ +", " ", data)
        data = re.sub('10#MS#GENRES###:','10#MS#GENRES####:', data)
        pri_indicator = len(re.findall("PRIMARY_VERSION", data)) > 20
        #print(data[:50])
        json_list = json.loads(data)
        # generate the corpus insights for this release:
        create_corpus_insights(json_list, release_obj, pri_indicator)
    if meta_upload:
        for d1 in json_list:
            try: 
                uri = d1["00#AUTH#URI######:"]
            except:
                uri = d1["00#LOC#URI#######:"]
            
            # for tests, only upload the metadata for authors 
            # who died between 300 and 325, and manuscript data:
            if test:
                date = int(re.findall(r"\d+", uri)[0])
                if (not uri.startswith("MS")) and (date < 310 or date > 310):
                    continue
                
            if uri.startswith("MS"):
                upload_ms_corpus_meta(d1, authorship_obj, release_obj, part_of_obj, 
                                      worldcat_obj, base_url, 
                                      release_info["release_code"])
            else:
                upload_book_corpus_meta(d1, authorship_obj, release_obj, part_of_obj, 
                                        book_type_obj, worldcat_obj, base_url, 
                                        release_info["release_code"])
                
    

    # with open(meta_fp, 'r', encoding='utf-8') as f:
    #     reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
    #     header = next(reader)
        
    #     for version_data in reader:
    #         # add the version_code + extension to the version_codes_d (to create the url to the text reuse data later)
    #         version_code = version_data["id"]
    #         try:
    #             version_codes_d[version_code] = re.findall(version_code+".*", version_data["url"])[0]
    #             # for text files that were split into parts, add the whole to the dictionary as well:
    #             if re.findall("[A-Z]$", version_code): 
    #                 whole_version_code = version_code[:-1]
    #                 s = version_codes_d[version_code]
    #                 whole_s = re.sub(version_code, whole_version_code, s)
    #                 version_codes_d[whole_version_code] = whole_s
    #                 print("add whole:", whole_version_code, whole_s)
    #         except: 
    #             print("version_code", version_code, "not found in url", version_data["url"])
            
    #         if not meta_upload:
    #             continue

    #         # for tests, only upload the metadata for authors 
    #         # between 300 and 325
    #         if test:
    #             #if not version_data["date"]:
    #             #    continue
    #             if version_data["date"] and (int(version_data["date"]) < 310 or int(version_data["date"]) > 310):
    #                 continue

    #         # read in the metadata for a version and format it:
    #         record = format_fields(version_data, base_url)
    #         print(version_data["versionUri"])

    #         if version_data["versionUri"].startswith("MS"):
    #             upload_ms_corpus_meta(record, authorship_obj, release_obj, book_type_obj, part_of_obj, worldcat_obj)
    #         else:
    #             upload_book_corpus_meta(record, authorship_obj, book_type_obj, release_obj, worldcat_obj)
    #         # # check if the version uri is already in the database:

    #         # #if True:  # TO DO replace with the try... except... block when folding in Versions:
    #         # try:
    #         #     vm = Version.objects.get(
    #         #         version_uri=record['version_uri']
    #         #     )
    #         # except Version.DoesNotExist:
    #         #     if VERBOSE:
    #         #         print(record['version_uri'], "does not exist in the database")

    #         #     # if not, check if the text author_uri is in the database:

    #         #     try:
    #         #         am = Author.objects.get(
    #         #             author_uri=record['author_uri']
    #         #         )
    #         #         if VERBOSE:
    #         #             print("but author does:", record['author_uri'])
    #         #     except:
    #         #         if VERBOSE:
    #         #             print("Author URI not in database either:", record['author_uri'])

    #         #         # the author is not yet in the database! Create a new author object:

    #         #         am, am_created = Author.objects.get_or_create(
    #         #             author_uri=record['author_uri'],
    #         #             tags=record['author_tags']
    #         #             # do not upload bibliography and notes
    #         #         )
    #         #         if am_created and VERBOSE:
    #         #             print("-> created", record['author_uri'])
                
    #         #     # Add names to the author object:
    #         #     add_author_names(am, record)
                
    #         #     # add dates related to the author:
    #         #     # first, create the date itself: 
    #         #     date_obj = get_or_create_date(
    #         #         date_type_slug="death_date",
    #         #         calendar_slug="hijri",
    #         #         date_str=record['author_uri'][:4],
    #         #         year=record['date'],
    #         #         precision="year",
    #         #         source="URI",
    #         #     )
    #         #     # then, add the link to the author:
    #         #     if date_obj:
    #         #         DateLink.objects.get_or_create(date=date_obj, author=am)
    #         #     else:
    #         #         failed_dates.add(record['author_uri'][:4])


    #         #     # the author is now in the database, check if the text exists:
                
    #         #     try:
    #         #         tm = Text.objects.get(
    #         #             text_uri=record['text_uri']
    #         #         )
    #         #         if VERBOSE:
    #         #             print("but text does:", record['text_uri'])
    #         #     except: 
    #         #         # the text is not yet in the database! Create a new text object:
    #         #         if VERBOSE:
    #         #             print("Text URI not in database either:", record['text_uri'])
    #         #         tm, tm_created = Text.objects.update_or_create(
    #         #             text_uri=record["text_uri"],
    #         #             #author=am,  # we add the author(s) with link_book_to_author
    #         #             defaults=dict(
    #         #                 tags=record["text_tags"]
    #         #             )
    #         #         )
    #         #         if tm_created and VERBOSE:
    #         #             print("-> created", record['text_uri'])
                
    #         #     link_book_to_author(tm, am, authorship_obj, authority="URI")
    #         #     link_book_to_titles(tm, record)
    #         #     add_book_type(tm, book_type_obj, source="URI")


    #         #     # now we are sure the author and text exist in the database, create a new version object:

    #         #     # (but first, we check if the edition meta object exists or create it)

    #         #     try:
    #         #         em = Edition.objects.filter(
    #         #             text=tm,
    #         #             ed_info=record['ed_info']
    #         #         )[0]  # more than one edition with the same query criteria may exist!; 
    #         #         # NB: .first() returns None if none exists, so it will not trigger the exception
    #         #         if VERBOSE:
    #         #             print("Edition does exist")
    #         #             print("em:", em)
    #         #             print()
    #         #     except: 
    #         #         if VERBOSE:
    #         #             print("Neither does the edition exist")



    #         #         em, em_created = Edition.objects.update_or_create(
    #         #             text=tm,
    #         #             ed_info=record["ed_info"],
    #         #         )
    #         #         # add worldcat link to external_ids:
    #         #         add_worldcat_id(em, record, worldcat_obj)
    #         #         if em_created and VERBOSE:
    #         #             print("-> Created Edition object")

    #         #     # now create the new version object:

    #         #     # upload the collection code if it doesn't exist yet:
    #         #     cm, cm_created = SourceCollectionDetails.objects.get_or_create(
    #         #         code=record["collection_code"]
    #         #     )

    #         #     if "part_of" in record:
    #         #         whole_obj = Version.objects.get(version_uri=record["part_of"])
    #         #     else:
    #         #         whole_obj = None

    #         #     vm, vm_created = Version.objects.update_or_create(
    #         #         version_code=record["version_code"],
    #         #         version_uri=record["version_uri"],
    #         #         text=tm,
    #         #         language=record["version_lang"],
    #         #         defaults=dict(
    #         #             edition=em,
    #         #             source_coll=cm,
    #         #             part_of=whole_obj
    #         #         )
    #         #     )     
    #         #     if vm_created and VERBOSE:
    #         #         print("-> created", record['version_uri'])              


    #         # # now that we know that the version object is in the database, 
    #         # # create or update the ReleaseVersion object:
    #         # rvm, rvm_created = ReleaseVersion.objects.update_or_create(
    #         #     release_info=release_obj,
    #         #     version=vm,
    #         #     defaults=dict(
    #         #         url=record["url"],
    #         #         char_length=record["char_length"],
    #         #         tok_length=record["tok_length"],
    #         #         analysis_priority=record["analysis_priority"],
    #         #         annotation_status=record["annotation_status"],
    #         #         tags=record["version_tags"]
    #         #     )
    #         # )
    #         # if rvm_created and VERBOSE:
    #         #     print("NEW RELEASE VERSION OBJECT CREATED:", rvm)

    print(f'Done uploading metadata for release {release_info["release_code"]}')
    print("OBJECTS CREATED:")
    print(json.dumps(IMPORT_STATS, indent=2))
    IMPORT_STATS.clear()
    logger.info(f'Done uploading metadata for release {release_info["release_code"]}')
    logger.info("OBJECTS CREATED:")
    for model,count in IMPORT_STATS.items():
        logger.info(f"- {count} {model} object(s)")
    if test:
        logger.warning("ONLY A TEST - NOT ALL METADATA UPLOADED!")


    return release_obj, version_codes_d

def add_insight(insights, key, languages, n=1):
    insights[key]["all"] =  insights[key]["all"] + n
    for lang in languages:
        insights[key][lang] = insights[key].get(lang, 0) + n

def create_corpus_insights(json_list, release_obj, pri_indicator=True):
    insights = dict(
        number_of_authors=0,
        number_of_books=0,
        number_of_versions={"all": 0},
        number_of_manuscript_holdings=0,
        number_of_manuscripts=0,
        number_of_pri_versions={"all": 0},
        number_of_sec_versions={"all": 0},
        number_of_markdown_versions={"all": 0},
        number_of_completed_versions={"all": 0},
        total_word_count={"all": 0},
        total_word_count_pri={"all": 0},
        largest_book_size=0,
        largest_book="",
        largest_10_books={}
    )
    pri_book_sizes = []
    book_sizes = []
    subcorpora = set()
    all_languages = set()
    has_manuscripts = False
    for d1 in json_list: 
        if "00#AUTH#URI######:" in d1:  # BOOK CORPUS !
            insights["number_of_authors"] += 1
            for book_d in d1.get("books", []):
                insights["number_of_books"] += 1
                pri_versions = get_pri_versions(book_d)
                for version_d in book_d.get("versions", []):
                    version_uri = version_d["00#VERS#URI######:"]
                    languages = re.findall("[a-z]{3}", version_uri.split("-")[-1])
                    for lang in languages:
                        subcorpora.add(lang)
                        all_languages.add(lang)
                    word_count = int(version_d.get("00#VERS#LENGTH###:"), 0)
                    book_sizes.append((word_count, version_uri))
                    add_insight(insights, "number_of_versions", languages)
                    add_insight(insights, "total_word_count", languages, word_count)
                    #if "PRIMARY_VERSION" in version_d.get("90#VERS#ISSUES###:", ""):
                    if version_uri in pri_versions:
                        add_insight(insights, "number_of_pri_versions", languages)
                        add_insight(insights, "total_word_count_pri", languages, word_count)
                        pri_book_sizes.append((word_count, version_uri))
                    else:
                        add_insight(insights, "number_of_sec_versions", languages)
                    extensions = version_d.get("extensions", [])
                    if ".completed" in extensions or "completed" in extensions:
                        add_insight(insights, "number_of_completed_versions", languages)
                    elif ".mARkdown" in extensions or "mARkdown" in extensions:
                        add_insight(insights, "number_of_markdown_versions", languages)

        elif "00#LOC#URI#######:" in d1:  # MANUSCRIPT CORPUS !
            insights["number_of_manuscript_holdings"] += 1
            subcorpora.add("MSS")
            has_manuscripts = True
            for ms_d in d1.get("manuscripts", []):
                pri_versions = get_pri_versions(ms_d)
                insights["number_of_manuscripts"] += 1
                for version_d in ms_d.get("transcriptions", []):
                    version_uri = version_d["00#TRNS#URI######:"]
                    languages = re.findall("[a-z]{3}", version_uri.split("-")[-1])
                    for lang in languages:
                        all_languages.add(lang)
                    word_count = int(version_d.get("00#TRNS#LENGTH###:"), 0)
                    book_sizes.append((word_count, version_uri))
                    add_insight(insights, "number_of_versions", languages)
                    add_insight(insights, "total_word_count", languages, word_count)
                    #if "PRIMARY_VERSION" in version_d.get("90#TRNS#ISSUES###:", ""):
                    if version_uri in pri_versions:
                        add_insight(insights, "number_of_pri_versions", languages)
                        add_insight(insights, "total_word_count_pri", languages, word_count)
                        pri_book_sizes.append((word_count, version_uri))
                    else:
                        add_insight(insights, "number_of_sec_versions", languages)
                    extensions = version_d.get("extensions", [])
                    if ".completed" in extensions or "completed" in extensions:
                        add_insight(insights, "number_of_completed_versions", languages)
                    elif ".mARkdown" in extensions or "mARkdown" in extensions:
                        add_insight(insights, "number_of_markdown_versions", languages)
        else:
            print("no URI in dictionary?", d)
    
    if len(pri_book_sizes) == 0:
        book_sizes.sort(reverse=True)
        largest_10_books = dict()
        book_uris = []
        for tok_count, version_uri in book_sizes:
            if len(largest_10_books) == 10:
                break
            book_uri = ".".join(version_uri.split(".")[:2])
            if book_uri not in book_uris:
                largest_10_books[version_uri] = tok_count
                book_uris.append(book_uri)
        pri_book_sizes = book_sizes
    else:
        pri_book_sizes.sort(reverse=True)
        largest_10_books = {tup[1]: tup[0] for tup in pri_book_sizes[:10]}
    insights["largest_10_books"] = largest_10_books
    insights["largest_book_size"] = pri_book_sizes[0][0]
    insights["largest_book"] = pri_book_sizes[0][1]
    insights["subcorpora"] = list(subcorpora)
    all_languages = {lang: f"{LANG_SCRIPT_NAMES[lang]} ({LANG_SCRIPT_DESCR[lang]})" for lang in all_languages}
    insights["languages"] = all_languages
    insights["has_manuscripts"] = has_manuscripts

    CorpusInsights.objects.get_or_create(
        release_info=release_obj,
        defaults=insights
    )
    IMPORT_STATS["corpusInsights"] = IMPORT_STATS.get("corpusInsights", 0) + 1

def get_pri_versions(d):
    version_list = d.get("versions", []) or d.get("transcriptions", [])
    
    # if there is only one version, it's primary by default:
    if len(version_list) == 1:
        version_uri = version_list[0].get("00#VERS#URI######:", "") \
                         or version_list[0].get("00#TRNS#URI######:", "")
        return [version_uri]
    elif version_list == []:
        return []

    # first, try to use the "PRIMARY_VERSION" issue:
    pri_versions = []
    uri_extensions = []
    for version_d in version_list:
        version_uri = version_d.get("00#VERS#URI######:", "") \
                         or version_d.get("00#TRNS#URI######:", "")
        version_issues = version_d.get("90#VERS#ISSUES###:", "") \
                         or version_d.get("90#TRNS#ISSUES###:", "")
        if "PRIMARY_VERSION" in version_issues:
            pri_versions.append(version_uri)
        uri_extensions.append((version_uri, version_d["extensions"]))
    
    if pri_versions != []:
        return pri_versions

    # if no version was selected as primary, use the file extensions:
    extensions_in_order = [".mARkdown", ".completed", ".inProgress",]
    for extension in extensions_in_order:
        for version_uri, extensions in uri_extensions:
            if extension in extensions:
                pri_versions.append(version_uri)
        if pri_versions != []:
            return pri_versions
    
    # if still no version was selected as primary: use the longest file:
    by_length = []
    for version_d in version_list:
        version_uri = version_d.get("00#VERS#URI######:", "") \
                         or version_d.get("00#TRNS#URI######:", "")
        length = version_d.get("00#VERS#LENGTH###:", "") \
                         or version_d.get("00#TRNS#LENGTH###:", "")
        by_length.append((length, version_uri))
    by_length.sort(reverse=True)
    for i in range(len(by_length)):
        version_uri = by_length[i][1]
        if "Sham30K" in version_uri:
            continue
        return [version_uri]
        




        

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
            