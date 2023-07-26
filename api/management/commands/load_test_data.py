
import json
import csv, io
from webbrowser import get
from django.db import models
from api.models import authorMeta, textMeta, versionMeta, personName, CorpusInsights, ReleaseMeta, ReleaseDetails, editionMeta, a2bRelation, relationType
from django.core.management.base import BaseCommand
import re
import random

import urllib.request
from django.contrib.auth.models import User


class Command(BaseCommand):

    def handle(self, **options):
        filename = '../OpenITI_metadata_2022-2-7_merged_wNoor.csv'
        #filename = 'https://raw.githubusercontent.com/OpenITI/kitab-metadata-automation/master/releases/OpenITI_metadata_2022-2-7_merged.csv'

        # with urllib.request.urlopen(filename) as url:
        #     data = url.read().decode('utf-8')
        # #filename = '../test.json'
        # superusers = User.objects.filter(is_superuser=True)
        # for user in superusers:
        #     print(user, superusers)
        # exit
        # ReleaseMeta.objects.all().delete()
        # textMeta.objects.all().delete()
        # authorMeta.objects.all().delete()
        # versionMeta.objects.all().delete()
        # personName.objects.all().delete()
        # ReleaseMeta.objects.all().delete()
        # editionMeta.objects.all().delete()
        # a2bRelation.objects.all().delete()
        # relationType.objects.all().delete()
        
        relations_definitions = "relations_definitions.tsv"
        main("muwatta_name_elements.tsv", "muwatta_relations_selection.json", "muwatta_selection.tsv")

        # read_json(filename)

def main(name_el_fp, book_rel_fp, meta_fp):
    name_el_d = load_name_elements(name_el_fp)
    book_rel_d = load_book_relations(book_rel_fp)
    load_main_data(meta_fp, name_el_d, book_rel_d)

def load_book_relations(book_rel_fp):
    with open(book_rel_fp, mode="r", encoding="utf-8") as file:
        book_rel_d = json.load(file)
    return book_rel_d

def load_name_elements(name_el_fp):
    fieldnames = "author_uri	language	ism	kunya	laqab	nasab	nisba	shuhra".split("\t")
    name_el_d = dict()
    with open(name_el_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
        d = next(reader)
        print(d)
        for data in reader:
            author_uri = data["author_uri"]
            if not author_uri in name_el_d:
                name_el_d[author_uri] = []
            name_el_d[author_uri].append(data)

    return name_el_d


def check_null(value):
    if value == '':
        return 0
    else:
        return value


def get_annotation_status(value):
    if value == 'mARkdown' or value == 'completed' or value == 'inProgress':
        return value
    else:
        return 'notYetAnnotated'


def get_version_lang(version_uri):
    try:
        return re.findall("-([a-z]{3})", version_uri)[0]
    except:
        return ""


def ah2ce(date):
    """convert AH date to CE date"""
    return 622 + (int(date) * 354 / 365.25)


def ce2ah(date):
    """convert CE date to AH date"""
    return (int(date) - 622) * 365.25 / 354


def get_authorDateAH(date, book_type):
    if book_type == "document":
        return ce2ah(date)
    return int(date)


def get_authorDateCE(date, book_type):
    if book_type != "document":
        return ah2ce(date)
    return int(date)


def load_main_data(meta_fp, name_el_d, book_rel_d):
    # create the release:
    release_id, created = ReleaseDetails.objects.update_or_create(
        release_code = "2022.2.7"
    )
    
    fieldnames = ['versionUri', 'date', 'author_ar', 'author_lat', 'book', 'title_ar', 'title_lat', 'ed_info', 'id', 'status', 'tok_length', 'url', 'tags', 'author_from_uri', 'author_lat_shuhra', 'author_lat_full_name', 'char_length']
    with open(meta_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')

        d = next(reader)
        print(d)
        for data in reader:
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
            record['titles_ar'] = data['title_ar']
            record['titles_lat'] = data['title_lat']
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

            # add/update the author meta to the database:

            author_uri = record['version_uri'].split(".")[0]
            am, am_created = authorMeta.objects.update_or_create(
                author_uri=author_uri,
                defaults = dict(
                    author_ar=record['author_ar'],
                    author_lat=record['author_lat'],
                    author_ar_prefered =record['author_ar_prefered'],
                    author_lat_prefered =record['author_lat_prefered'],
                    date=record['date'],
                    date_AH=get_authorDateAH(record['date'], record['type']),
                    date_CE=get_authorDateCE(record['date'], record['type']),
                    date_str=str(record['date'])
                )
            )

            # add/update the author's name elements to the database (only once)
            if author_uri in name_el_d:
                for d in name_el_d[author_uri]:
                    personName.objects.update_or_create(
                        author_meta=am,
                        language=d["language"],
                        defaults=dict(
                            shuhra=d["shuhra"],
                            kunya=d["kunya"],
                            ism=d["ism"],
                            laqab=d["laqab"],
                            nisba=d["nisba"]
                        )
                    )
                del name_el_d[author_uri]

            # add/update the text metadata:
            text_uri = record['text_uri']
            tm, tm_created = textMeta.objects.update_or_create(
                author_meta =am,
                text_uri=text_uri,
                defaults=dict(
                    titles_ar=record['titles_ar'],
                    titles_lat=record['titles_lat'],
                    title_ar_prefered = record['title_ar_prefered'],
                    title_lat_prefered = record['title_lat_prefered'],
                    text_type=record["type"],
                    tags=record["tags"]
                )
            )
            print(tm, tm_created)

            # add the book relations data:
            if text_uri in book_rel_d:
                for d in book_rel_d[text_uri]:
                    # add the relation type if it doesn't exist yet:
                    main_rel_type = d["main_rel_type"]
                    sec_rel_type = d["sec_rel_type"]
                    mr, mr_created = relationType.objects.get_or_create(code=main_rel_type, subtype_code=sec_rel_type)
                    # check whether the text_uri is the source or target element:
                    if d["source"] == text_uri:
                        text_a = tm
                        text_b, created = textMeta.objects.get_or_create(
                            text_uri=d["dest"]
                        )

                    else:
                        text_a, created = textMeta.objects.get_or_create(
                            text_uri=d["dest"]
                        )
                        text_b = tm
                    
                    a2bRelation.objects.update_or_create(
                        text_a=text_a,
                        text_b=text_b,
                        defaults=dict(
                            relation_type=mr
                        )
                    )
                
            # add the edition if one is mentioned:
            if record['ed_info']:
                em, em_created = editionMeta.objects.update_or_create(
                    text_meta=tm,
                    ed_info=record['ed_info'],
                )
            else:
                em = None

            vm, vm_created = versionMeta.objects.update_or_create(
                text_meta=tm,
                version_id=record['version_id'],
                version_uri=record['version_uri'],
                defaults=dict(
                    tags=record['tags'],
                    language=record['version_lang'],
                    edition_meta=em
                )
            )
            print(vm, vm_created)

            ReleaseMeta.objects.update_or_create(
                release = release_id,
                version_meta= vm,
                defaults=dict(
                    char_length=record['char_length'],
                    tok_length=record['tok_length'],
                    url=record['url'],
                    annotation_status=record['annotation_status'],
                    analysis_priority=record['analysis_priority']
                )
            )
