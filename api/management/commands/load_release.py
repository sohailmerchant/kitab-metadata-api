"""THIS SCRIPT IS WORK IN PROGRESS - DO NOT USE YET

This script uploads the metadata of the 2022.1.6 release to the database.
"""

import csv
from webbrowser import get
from django.db import models
from api.models import authorMeta, textMeta, versionMeta, CorpusInsights, ReleaseMeta, ReleaseDetails, editionMeta, TextReuseStats, SourceCollectionDetails
from django.core.management.base import BaseCommand
import re
import datetime
import json

version_ids = dict()

class Command(BaseCommand):
    def handle(self, **options):
        # if testing, only upload text reuse data for Tabari.Tarikh and MalikIbnAnas.Muwatta
        test = True

        # provide the release details here:

        release_code = "2022.2.7"
        release_date = datetime.date(2023, 2, 24) # YYYY, M, D
        meta_fp = "meta/OpenITI_metadata_2022-2-7_merged_wNoor.csv"
        base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.2.7/data"
        zenodo_link = "https://zenodo.org/record/7687795"
        release_notes_fp = "meta/release_notes_2022-2-7.txt"
        reuse_data_fp = "reuse_data/stats-v2022-2-7_bi-dir.csv"
        reuse_data_base_url = "http://dev.kitab-project.org/passim01122022/"

        # release_code = "2022.1.6"
        # release_date = datetime.date(2022, 7, 8) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2022-1-6_merged_wNoor.csv"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.1.6/data"
        # zenodo_link = "https://zenodo.org/record/6808108"
        # release_notes_fp = "meta/release_notes_2022-1-6.txt"
        # reuse_data_fp = "reuse_data/stats-v2022-1-6_bi-dir.csv"
        # reuse_data_base_url = "http://dev.kitab-project.org/passim01102022/"

        # release_code = "2021.2.5"
        # release_date = datetime.date(2021, 10, 18) # YYYY, M, D
        # meta_fp = "meta/OpenITI_metadata_2021-2-5_merged_wNoor.csv"
        # base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2021.2.5/data"
        # zenodo_link = "https://zenodo.org/record/5550338"
        # release_notes_fp="meta/release_notes_2021-2-5.txt"
        # reuse_data_fp = "reuse_data/stats-v2021-2-5_bi-dir.csv"
        # reuse_data_base_url = "http://dev.kitab-project.org/passim01102021/"


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

        main(meta_fp, base_url, release_info, reuse_data_fp, reuse_data_base_url, test=test)


def main(meta_fp, base_url, release_info, reuse_data_fp, reuse_data_base_url, test=False):
    # load the release metadata:
    release_obj, version_ids_d = upload_release_meta(meta_fp, base_url, release_info)
    # check for duplicate version_ids:
    no_duplicates=True
    for version_id, fn_list in version_ids.items():
        if len(fn_list) > 1:
            print("DUPLICATE ID:", version_id)
            print(fn_list)
            no_duplicates = False
    if no_duplicates:
        print("No duplicate version IDs found")
    # upload the text reuse stats:
    
    upload_reuse_stats(reuse_data_fp, release_info["release_code"], release_obj, reuse_data_base_url, version_ids_d, test=test)
    # create the corpus insights data:
    

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

def ah2ce(date):
    """convert AH date to CE date"""
    return 622 + (int(date) * 354 / 365.25)

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
        elif "NO_MAJOR_ISSUES" in tag:
            version_tags.append("NO_MAJOR_ISSUES")
        elif "born@" in tag or "died@" in tag or "resided@" in tag or "visited@" in tag:
            author_tags.append(tag)
        elif "@" in tag or tag.startswith("_"):
            text_tags.append(tag)
        else:
            version_tags.append(tag)
    return version_tags, text_tags, author_tags
        
def format_fields(data, base_url):
    record = dict()
    
    record['version_uri'] = data['versionUri']
    record['version_lang'] = get_version_lang(record['version_uri'])
    record['date'] = int(data['date'])
    record['date_AH'] = int(data['date'])
    record['date_CE'] = ah2ce(data['date'])
    record['date_str'] = int(data['date'])
    record['author_ar'] = data['author_ar']
    record['author_lat'] = data['author_lat']
    record['author_ar_prefered'] = re.split(' *:: *| *, *| *; *',data['author_ar'])[0]

    if data['author_lat_shuhra']:
        record['author_lat_prefered'] = re.split(' *:: *| *, *| *; *',data['author_lat_shuhra'])[0]
    else:
        record['author_lat_prefered'] = re.split(' *:: *| *, *| *; *',data['author_lat'])[0]

    record['text_uri'] = data['book']
    record['author_uri'] = data['book'].split(".")[0]
    record['titles_ar'] = data['title_ar']
    record['titles_lat'] = data['title_lat']
    record['title_ar_prefered'] = re.split(' *:: *| *, *| *; *',data['title_ar'])[0]
    record['title_lat_prefered'] = re.split(' *:: *| *, *| *; *',data['title_lat'])[0]
    record['ed_info'] = data['ed_info']
    record['version_id'] = data['id']
    try:
        record["collection_code"] = re.findall(r"^([A-Za-z]+?\d*[A-Za-z]+)\d+(?:BK\d+)?(?:Vols)?[A-Z]?$", data['id'])[0]
    except:
        record["collection_code"] = None
        print("Collection code not found in", data['id'])
        input("CONTINUE?")
    version_tags, text_tags, author_tags = split_tag_list(data['tags'].split(" :: "))
    record["version_tags"] = " :: ".join(version_tags)
    record["text_tags"] = " :: ".join(text_tags)
    record["author_tags"] = " :: ".join(author_tags)
    

    record['author_from_uri'] = data['author_from_uri']
    record['author_lat_shuhra'] = data['author_lat_shuhra']
    record['author_lat_full_name'] = data['author_lat_full_name']

    ##releasefields
    record['char_length'] = data['char_length']
    record['tok_length'] = data['tok_length']
    record['url'] = data['url'].replace("../data", base_url)
    record['analysis_priority'] = data['status']
    record['annotation_status'] = get_annotation_status(data['url'].split('.')[-1])
    if "type" in data:
        record["type"] = data["type"]
    else:
        record["type"] = "book"

    return record


def upload_release_meta(meta_fp, base_url, release_info):
    version_ids_d = dict()
    fieldnames = ['versionUri', 'date', 'author_ar', 'author_lat', 'book', 'title_ar', 'title_lat', 'ed_info', 'id', 'status', 'tok_length', 'url', 'tags', 'author_from_uri', 'author_lat_shuhra', 'author_lat_full_name', 'char_length']
    with open(meta_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
        header = next(reader)

        for version_data in reader:
            # add the version_id + extension to the version_ids_d (to create the url to the text reuse data later)
            version_id = version_data["id"]
            try:
                version_ids_d[version_id] = re.findall(version_id+".*", version_data["url"])[0]
            except: 
                print("version_id", version_id, "not found in url", version_data["url"])

            # read in the metadata for a version and format it:
            record = format_fields(version_data, base_url)

            # first, create the new release itself in the database:

            release_obj, created = ReleaseDetails.objects.update_or_create(
                release_code=release_info["release_code"],
                defaults=dict(
                    release_date=release_info["release_date"],
                    zenodo_link=release_info["zenodo_link"],
                    release_notes=release_info["release_notes"]
                )
            )

            # check if the version uri is already in the database:

            try:
                vm = versionMeta.objects.get(
                    version_uri=record['version_uri'],
                    language=record["version_lang"]
                )
            except versionMeta.DoesNotExist:
                print(record['version_uri'], "does not exist in the database")

                # if not, check if the text author_uri is in the database:

                try:
                    am = authorMeta.objects.get(
                        author_uri=record['author_uri']
                    )
                    print("but author does:", record['author_uri'])
                except:
                    print("Author URI not in database either:", record['author_uri'])

                    # the author is not yet in the database! Create a new author object:

                    am, am_created = authorMeta.objects.get_or_create(
                        author_uri=record['author_uri'],
                        author_ar=record['author_ar'],
                        author_lat=record['author_lat'],
                        author_ar_prefered =record['author_ar_prefered'],
                        author_lat_prefered =record['author_lat_prefered'],
                        date=record['date'],
                        date_AH=record['date_AH'],
                        date_CE=record['date_CE'],
                        date_str=record['date_str'],
                        tags=record['author_tags']
                        # do not upload bibliography and notes
                    )
                    if am_created:
                        print("-> created", record['author_uri'])

                # the author is now in the database, check if the text exists:

                try:
                    tm = textMeta.objects.get(
                        text_uri=record['text_uri']
                    )
                    print("but text does:", record['text_uri'])
                except: 
                    # the text is not yet in the database! Create a new text object:
                    print("Text URI not in database either:", record['text_uri'])
                    tm, tm_created = textMeta.objects.update_or_create(
                        text_uri=record["text_uri"],
                        author_meta=am,
                        defaults=dict(
                            titles_ar=record['titles_ar'],
                            titles_lat=record['titles_lat'],
                            title_ar_prefered = record['title_ar_prefered'],
                            title_lat_prefered = record['title_lat_prefered'],
                            text_type="book",
                            tags=record["text_tags"],
                        )
                    )
                    if tm_created:
                        print("-> created", record['text_uri'])


                # now we are sure the author and text exist in the database, create a new version object:

                # (but first, we check if the edition meta object exists or create it)

                try:
                    em = editionMeta.objects.filter(
                        text_meta=tm,
                        ed_info=record['ed_info']
                    )[0]  # more than one edition with the same query criteria may exist!; 
                    # NB: .first() returns None if none exists, so it will not trigger the exception
                    print("Edition does exist")
                    print("em:", em)
                    print()
                except: 
                    print("Neither does the edition exist")

                    em, em_created = editionMeta.objects.update_or_create(
                        text_meta=tm,
                        ed_info=record["ed_info"],
                    )
                    if em_created:
                        print("-> Created Edition object")

                # now create the new version object:

                # upload the collection code if it doesn't exist yet:
                cm, cm_created = SourceCollectionDetails.objects.get_or_create(
                    code=record["collection_code"]
                )

                vm, vm_created = versionMeta.objects.update_or_create(
                    version_id=record["version_id"],
                    version_uri=record["version_uri"],
                    text_meta=tm,
                    language=record["version_lang"],
                    defaults=dict(
                        edition_meta=em,
                        source_coll=cm
                    )
                )     
                if vm_created:
                    print("-> created", record['version_uri'])              


            # now that we know that the version object is in the database, create or update the ReleaseMeta object:
            # TO DO: 
            rvm, rvm_created = ReleaseMeta.objects.update_or_create(
                release=release_obj,
                version_meta=vm,
                defaults=dict(
                    url=record["url"],
                    char_length=record["char_length"],
                    tok_length=record["tok_length"],
                    analysis_priority=record["analysis_priority"],
                    annotation_status=record["annotation_status"],
                    tags=record["version_tags"]
                )
            )

    return release_obj, version_ids_d
 
def upload_reuse_stats(reuse_data_fp, release_code, release_obj, reuse_data_base_url, version_ids_d, test=False):
    with open(reuse_data_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for data in reader:
            if test:
                # for testing: only load 0179MalikIbnAnas.Muwatta and 0310Tabari.Tarikh stats:
                if not (("Shamela0009783" in data['_T1'] or "Shamela0009783" in data['_T2']) \
                    or ("Shamela0028107" in data['_T1'] or "Shamela0028107" in data['_T1'])):  # 0179MalikIbnAnas.Muwatta
                    continue
            version_id1 = data['_T1'].split("-")[0].split(".")[0]
            version_id2 = data['_T2'].split("-")[0].split(".")[0]
            # get the last part of the filename (version_id + lang + number + extension),
            # which form part of the URL
            try:
                ref1 = version_ids_d[version_id1]
                ref2 = version_ids_d[version_id2]
            except:
                print("FAILED:", version_id1, version_id2)
            b1 = ReleaseMeta.objects.get(
                    release__release_code=release_code,
                    version_meta__version_id=version_id1
                    )
            b2 = ReleaseMeta.objects.get(
                    release__release_code=release_code,
                    version_meta__version_id=version_id2
                    )
            
            tsv_url = f"{reuse_data_base_url}{ref1}/{ref1}_{ref2}.csv"
            
            TextReuseStats.objects.update_or_create(
                book_1 = b1,
                book_2 = b2,
                instances_count=data['instances'],
                book1_words_matched=data['WM1_Total'],
                book2_words_matched=data['WM2_Total'],
                book1_pct_words_matched=data['WM_B1inB2'],
                book2_pct_words_matched=data['WM_B2inB1'],
                release=release_obj,
                defaults=dict(
                    tsv_url=tsv_url
                )
            )