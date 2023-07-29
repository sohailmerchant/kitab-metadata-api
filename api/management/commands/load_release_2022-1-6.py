"""THIS SCRIPT IS WORK IN PROGRESS - DO NOT USE YET

This script uploads the metadata of the 2022.1.6 release to the database.
"""

import json
import csv
from webbrowser import get
from django.db import models
from api.models import authorMeta, textMeta, versionMeta, personName, CorpusInsights, ReleaseMeta, ReleaseDetails, editionMeta, a2bRelation, relationType, placeMeta
from django.core.management.base import BaseCommand
import os
import re
import random
import itertools
import datetime

from openiti.git import get_issues   # TO DO: add issues!
from openiti.helper.yml import readYML, dicToYML, fix_broken_yml
from openiti.helper.ara import deNoise, ar_cnt_file

from api.betaCode import betaCodeToArSimple

version_ids = dict()

release_notes = """\
OpenITI: a Machine-Readable Corpus of Islamicate Texts
Nigst, Lorenz; Romanov, Maxim; Savant, Sarah Bowen; Seydi, Masoumeh; Verkinderen, Peter

Co-PIs: Matthew Thomas Miller (University of Maryland, College Park), Maxim G. Romanov (University of Vienna), Sarah Bowen Savant (Aga Khan University—ISMC, London).

Open Islamicate Texts Initiative (OpenITI, see https://iti-corpus.github.io/) is a multi-institutional effort to construct the first machine-actionable scholarly corpus of premodern Islamicate texts. Led by researchers at the Aga Khan University, Institute for the Study of Muslim Civilisations (AKU-ISMC), University of Vienna (UV), Leipzig University (LU), and the Roshan Institute for Persian Studies at the University of Maryland (College Park) and an interdisciplinary advisory board of leading digital humanists and Islamic, Persian, and Arabic studies scholars, OpenITI aims to provide the essential textual infrastructure in Arabic, Persian and other Islamicate languages for new forms of textual analysis and digital scholarship. In the process, OpenITI will enable new synergies between Digital Humanities and the inter-related Islamicate fields of Islamic, Persian, and Arabic Studies. In addition to support from the researchers’ home institutions, it is supported by funding from the European Research Council under the European Union’s Horizon 2020 research and innovation programme, awarded to the KITAB project (Grant Agreement No. 772989, PI Sarah Bowen Savant) and the Qatar National Library.

Currently, OpenITI contains almost exclusively Arabic texts, which were first assembled into a corpus within the OpenArabic project, developed first at Tufts University (at The Perseus Project, 2013–2015) and then at Leipzig University (at the Alexander von Humboldt Chair for Digital Humanities, 2015–2017)—in both cases with the support and under the patronage of Prof. Gregory Crane. The much more limited number of Persian texts were compiled during 2015–2016 in the Persian Digital Library (PDL) pilot (see Persian Digital Library by PersDigUMD) at Roshan Institute for Persian Studies at the University of Maryland. These texts have not been made fully compatible with OpenITI mARkdown yet and will be made fully available in next releases.

Note on Release Numbering: Version 2019.1.1—where 2019 is the year of the release, the first dotted number—.1—is the ordinal release number in 2019, and the second dotted number—.1—is the overall release number; the first dotted number will reset every year, while the second one will continue on increasing.

For more details: https://github.com/OpenITI/RELEASE
"""

class Command(BaseCommand):
    def handle(self, **options):
        meta_fp = "OpenITI_metadata_2022-1-6_merged.csv"
        base_url = "https://raw.githubusercontent.com/OpenITI/RELEASE/v2022.1.6/data"
        release_info = dict(
            release_code="2022.1.6",
            release_date=datetime.date(2022, 7, 8), # YYYY, M, D
            zenodo_link="https://zenodo.org/record/6808108",
            release_notes=release_notes,
        )

        main(meta_fp, base_url, release_info)


def main(meta_fp, base_url, release_info):
    # load the release metadata:
    upload_from_csv(meta_fp, base_url, release_info)
    # check for duplicate version_ids:
    for version_id, fn_list in version_ids.items():
        if len(fn_list) > 1:
            print("DUPLICATE ID:", version_id)
            print(fn_list)

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


def upload_from_csv(meta_fp, base_url, release_info):
    fieldnames = ['versionUri', 'date', 'author_ar', 'author_lat', 'book', 'title_ar', 'title_lat', 'ed_info', 'id', 'status', 'tok_length', 'url', 'tags', 'author_from_uri', 'author_lat_shuhra', 'author_lat_full_name', 'char_length']
    with open(meta_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
        header = next(reader)

        for version_data in reader:

            # read in the metadata for a version and format it:
            record = format_fields(version_data, base_url)

            if record["version_uri"] == "0775IbnAbiWafa.JawahirMudiya.JK000806-ara1":
                print("0775IbnAbiWafa.JawahirMudiya.JK000806-ara1")
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

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

                vm, vm_created = versionMeta.objects.update_or_create(
                    version_id=record["version_id"],
                    version_uri=record["version_uri"],
                    text_meta=tm,
                    language=record["version_lang"],
                    defaults=dict(
                        edition_meta=em,
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
 
