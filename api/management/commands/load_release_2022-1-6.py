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
            release_date=datetime.date(2022, 7, 8), # YYYY M D
            zenodo_link="https://zenodo.org/record/6808108",
            release_notes=release_notes
        )

        main(meta_fp, base_url, release_info)


def main(meta_fp, base_url, release_info):
    # load the release metadata:
    read_csv(meta_fp, base_url, release_info)
    # check for duplicate version_ids:
    for version_id, fn_list in version_ids.items():
        if len(fn_list) > 1:
            print("DUPLICATE ID:", version_id)
            print(fn_list)

def read_csv(meta_fp, base_url, release_info):
    with open(meta_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for data in reader:

            # read in the metadata for a version and format it:

            record = dict()
            
            record['version_uri'] = data['versionUri']
            record['version_lang'] = get_version_lang(record['version_uri'])
            record['date'] = data['date']
            record['author_ar'] = data['author_ar']
            record['author_lat'] = data['author_lat']
            record['author_ar_prefered'] = re.split(' *:: *| *, *| *; *',data['author_ar'])[0]

            if data['author_lat_shuhra']:
                record['author_lat_prefered'] = re.split(' *:: *| *, *| *; *',data['author_lat_shuhra'])[0]
            else:
                record['author_lat_prefered'] = re.split(' *:: *| *, *| *; *',data['author_lat'])[0]

            record['text_uri'] = data['book']
            record['author_uri'] = data['book'].split(".")[0]
            record['title_ar'] = data['title_ar']
            record['title_lat'] = data['title_lat']
            record['title_ar_prefered'] = re.split(' *:: *| *, *| *; *',data['title_ar'])[0]
            record['title_lat_prefered'] = re.split(' *:: *| *, *| *; *',data['title_lat'])[0]
            record['ed_info'] = data['ed_info']
            record['version_id'] = data['id']
            record['tags'] = data['tags']
            record['author_from_uri'] = data['author_from_uri']
            record['author_lat_shuhra'] = data['author_lat_shuhra']
            record['author_lat_full_name'] = data['author_lat_full_name']

            ##releasefields
            record['tok_length'] = check_null(data['tok_length'])
            record['url'] = data['url']
            record['analysis_priority'] = data['status']
            record['char_length'] = check_null(data['char_length'])
            record['annotation_status'] = get_annotation_status(
                data['url'].split('.')[-1])
            if "type" in data:
                record["type"] = data["type"]
            else:
                record["type"] = "book"

            # load the metadata into the database: 

            release_obj, created = ReleaseDetails.objects.update_or_create(
                release_code=release_info["release_code"],
                defaults=dict(
                    release_date=release_info["release_date"],
                    zenodo_link=release_info["zenodo_link"],
                    release_notes=release_info["release_notes"]
                )
            )

            try:
                # check if the version uri is already in the database:
                vm = versionMeta.objects.get(
                    version_uri=record['version_uri']
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
                    # the author is not yet in the database! Create a new author object:
                    # TO DO
                    # am = authorMeta.object.create()
                    print("Auhtor URI not in database either:", record['author_uri'])

                # the author is already in the database, check if the text exists:
                try:
                    tm = textMeta.objects.get(
                        text_uri=record['text_uri']
                    )
                    print("but text does:", record['text_uri'])
                except: 
                    # the text is not yet in the database! Create a new text object:
                    # TO DO
                    # tm = textMeta.object.create()
                    print("Text URI not in database either:", record['text_uri'])

                # now we are sure the author and text exist in the database, create a new version object:
                # TO DO: 
                # vm = versionMeta.object.create()
                # rm = ReleaseMeta.object.create()

            # now that we know that the version object is in the database, create or update the ReleaseMeta object:
            # TO DO: 
            # rm, created = ReleaseMeta.object.update_or_create(
            #     ...,
            #     defaults=dict(
            #         ...
            #     )
            # )

            # print(authorMeta.objects.filter(author_uri = "0001AbuTalibCabdManaf").exists())
            # never create duplicate author data, except for Anonymous authors:

            # author_uri = record['version_uri'].split(".")[0]
            # if re.findall('\d{4}Anonymous\.', author_uri):
            #     create_new = True
            # else:
            #     if not authorMeta.objects.filter(author_uri=author_uri).exists():
            #         create_new = True
            #     else:
            #         create_new = False
            # if create_new:
            #     am, am_created = authorMeta.objects.get_or_create(

            #         author_uri=record['version_uri'].split(".")[0],
            #         author_ar=record['author_ar'],
            #         author_lat=record['author_lat'],
            #         author_ar_prefered =record['author_ar_prefered'],
            #         author_lat_prefered =record['author_lat_prefered'],
            #         date=record['date'],
            #         authorDateAH=get_authorDateAH(
            #             record['date'], record['type']),
            #         authorDateCE=get_authorDateCE(
            #             record['date'], record['type']),
            #         authorDateString=str(record['date'])

            #     )
            # else:
               
            #     # am = authorMeta.objects.filter(author_uri=author_uri).update(

            #     #     #author_uri=record['version_uri'].split(".")[0],
                 
            #     #     author_ar=record['author_ar'],
            #     #     author_lat=record['author_lat'],
            #     #     date=record['date'],
            #     #     authorDateAH=get_authorDateAH(
            #     #         record['date'], record['type']),
            #     #     authorDateCE=get_authorDateCE(
            #     #         record['date'], record['type']),
            #     #     authorDateString=str(record['date'])
                    
              
            #     # )
            #     am = authorMeta.objects.filter(
            #     author_uri=record['version_uri'].split(".")[0]).first()
            #     am_created = False
            #     # am = authorMeta.objects.filter(id=am)
            #     # print(am)
            # if not textMeta.objects.filter(text_uri=record['text_uri']).exists():
                
            #     item, created = textMeta.objects.get_or_create(
            #         #author_uri=am,
            #         author_id =am,
            #         text_uri=record['text_uri'],
            #         title_ar=record['title_ar'],
            #         title_lat=record['title_lat'],
            #         title_ar_prefered = record['title_ar_prefered'],
            #         title_lat_prefered = record['title_lat_prefered'],
            #         text_type=record["type"],
            #         tags=record["tags"]
            #     )
            #     print(item, created)
            # else:
            #     created = False
            #     item = textMeta.objects.filter(
            #         text_uri=record['text_uri']).first()
            #     # item = textMeta.objects.filter(text_uri=record['text_uri']).update(
            #     #     #author_uri=am,
            #     #     author_id =am,
                
            #     #     text_uri=record['text_uri'],
            #     #     title_ar=record['title_ar'],
            #     #     title_lat=record['title_lat'],
            #     #     title_ar_prefered = record['title_ar_prefered'],
            #     #     title_lat_prefered = record['title_lat_prefered'],
            #     #     text_type=record["type"],
            #     #     tags=record["tags"]
                
            #     # )
            #     # item = textMeta.objects.filter(id=item)
            #     # print(item)


            # if not versionMeta.objects.filter(version_uri=record['version_uri']).exists():
            #     item, created = versionMeta.objects.get_or_create(
            #         text_id=item,
            #         version_id=record['version_id'],
            #         version_uri=record['version_uri'],
            #         ed_info=record['ed_info'],
            #         tags=record['tags'],
            #         version_lang=record['version_lang']
            #     )
            #     print(item, created)
            # else:
            #     item = versionMeta.objects.filter(
            #         version_uri=record['version_uri']).first()

            # ReleaseMeta.objects.get_or_create(
            #     release_code = '2022.2.7',
            #     version_uri= item,
            #     char_length=record['char_length'],
            #     tok_length=record['tok_length'],
            #     url=record['url'],
            #     annotation_status=record['annotation_status'],
            #     analysis_priority=record['analysis_priority']

            # )

            # # name elements are not separately in the metadata file as it is now;
            # # loading bogus data for now!
            # if am_created:
            #     for lan in ("ar", "lat"):
            #         name_elements = re.split(" *:: *", record['author_'+lan])
            #         while len(name_elements) < 5:
            #             name_elements.append("")
            #         random.shuffle(name_elements)

            #         personName.objects.get_or_create(
            #             author_id=am,
            #             language=lan,
            #             shuhra=name_elements[0],
            #             kunya=name_elements[1],
            #             ism=name_elements[2],
            #             laqab=name_elements[3],
            #             nisba=name_elements[4],
            #         )
 
