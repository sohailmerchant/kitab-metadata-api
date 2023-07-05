
import json, csv
from webbrowser import get
from django.db import models
from api.models import authorMeta, textMeta, versionMeta, personName, relationType, a2bRelation  #, AggregatedStats
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re
import random

import urllib.request



class Command(BaseCommand):
    def handle(self, **options):
       
        # with urllib.request.urlopen(filename) as url:
        #     data = url.read().decode('utf-8')
        # #filename = '../test.json'
        
        #textMeta.objects.all().delete()
        #authorMeta.objects.all().delete()
        #versionMeta.objects.all().delete()
        #personName.objects.all().delete()
        #relationType.objects.all().delete()
        a2bRelation.objects.all().delete()

        # load relation types:
        relation_types_fn = "relationTypes.tsv"
        fp = os.path.join(settings.BASE_DIR, relation_types_fn)
        print(fp)
        load_relation_types(fp)

        
 
        filename = 'OpenITI_Github_clone_metadata_light.csv'
        fp  = os.path.join(settings.BASE_DIR, filename)
        print(fp)
        records = read_csv(fp)
        #load_records(records)
        book_uris = set([d['text_uri'] for d in records])



        #book_relations_fn = "OpenITI_Github_clone_book_relations.json"
        book_relations_fn = "OpenITI_Github_clone_book_relations_selection.json"
        fp  = os.path.join(settings.BASE_DIR, book_relations_fn)
        print(fp)
        with open(fp, mode="r", encoding="utf-8") as file:
            data = json.load(file)
        book_uri_not_in_corpus = []
        for book_uri in data:
            if book_uri not in book_uris:
                book_uri_not_in_corpus.append(book_uri)
        if book_uri_not_in_corpus:
            print("These book uris from the book relations file are not in the corpus:")
            for b in book_uri_not_in_corpus:
                print("*", b)
            input("Fix these before loading the book relations!")
        load_book_relations(fp)
        
        name_elements_fn = "OpenITI_Github_clone_name_elements.json"
        fp  = os.path.join(settings.BASE_DIR, name_elements_fn)
        load_name_elements(fp)

def load_relation_types(fp):
    with open(fp, mode="r", encoding="utf-8") as file:
        d = csv.DictReader(file, delimiter="\t")
        for row in d:
            rtype, created = relationType.objects.get_or_create(
                    name = row["name"],
                    name_inverted = row["name_inverted"],
                    descr = row["descr"],
                    code = row["code"],
                    entities = row["entities"],
                )

def load_name_elements(fp):
    languages = {"AR": "ara", "EN": "eng", "FA": "per", "PE": "per", "LA": "lat"}
    with open(fp, mode="r", encoding="utf-8") as file:
        data = json.load(file)
    for author_uri in data:
        author_id, created = authorMeta.objects.get_or_create(
            author_uri = author_uri
        )
        print(author_uri, "created:", created)
        for lang, d in data[author_uri].items():
            lang_code = languages[lang]
            print(d)
            name, created = personName.objects.get_or_create(
                author_id = author_id,
                language = lang_code,
                shuhra = d["shuhra"],
                nasab = d["nasab"],
                kunya = d["kunya"],
                ism = d["ism"],
                laqab = d["laqab"],
                nisba = d["nisba"]
            )
            if lang_code not in ["eng", "lat"]:
                norm, created = personName.objects.get_or_create(
                    author_id = author_id,
                    language = "arn",       # normalized Arabic script
                    shuhra = d["shuhra"],   
                    nasab = d["nasab"],
                    kunya = d["kunya"],
                    ism = d["ism"],
                    laqab = d["laqab"],
                    nisba = d["nisba"]
                )


def load_book_relations(fp):
    created_objects = []
    with open(fp, mode="r", encoding="utf-8") as file:
        data = json.load(file)
    for book_uri in data:
        print(book_uri)
        print(data[book_uri])
        for rel_d in data[book_uri]:
            code = ".".join([rel_d["main_rel_type"], rel_d["sec_rel_type"].lower()])
            # create the main relation type in the relationType table if it does not exist yet:
            print("code:", code)
            rt,rt_created = relationType.objects.get_or_create(
                code = code
            )
            if rt_created:
                created_objects.append(code)
            a = rel_d["source"]
            if len(a.split(".")) > 1:
                a_type = "book"
            else:
                a_type = "person"
            print("a=source:", a, a_type)
            b = rel_d["dest"]
            if len(b.split(".")) > 1:
                b_type = "book"
            else:
                b_type = "person"
            print("b=dest:", b, b_type)
            if a_type == "book" and b_type == "book":
                a_author, author_created = authorMeta.objects.get_or_create(
                    author_uri = a.split(".")[0]
                )
                if author_created:
                    created_objects.append(a.split(".")[0])
                a_obj, a_created = textMeta.objects.get_or_create(
                    text_uri = a,
                    author_id = a_author
                )
                if a_created:
                    created_objects.append(a)
                b_author, author_created = authorMeta.objects.get_or_create(
                    author_uri = b.split(".")[0]
                )
                if author_created:
                    created_objects.append(b.split(".")[0])
                b_obj, b_created = textMeta.objects.get_or_create(
                    text_uri = b,
                    author_id = b_author
                )
                if b_created:
                    created_objects.append(b)
                a2bRelation.objects.get_or_create(
                    text_a_id = a_obj,
                    text_b_id = b_obj,
                    relation_type = rt
                )
            elif a_type == "person" and b_type == "book":
                a_obj, a_created = authorMeta.objects.get_or_create(
                    author_uri = a 
                )
                if a_created:
                    created_objects.append(a)
                b_author, author_created = authorMeta.objects.get_or_create(
                    author_uri = b.split(".")[0]
                )
                if author_created:
                    created_objects.append(b.split(".")[0])
                b_obj, b_created = textMeta.objects.get_or_create(
                    text_uri = b,
                    author_id = b_author
                )
                a2bRelation.objects.get_or_create(
                    person_a_id = a_obj,
                    text_b_id = b_obj,
                    relation_type = rt
                )
            elif a_type == "book" and b_type == "person":
                a_author, author_created = authorMeta.objects.get_or_create(
                    author_uri = a.split(".")[0]
                )
                if author_created:
                    created_objects.append(a.split(".")[0])
                a_obj, a_created = textMeta.objects.get_or_create(
                    text_uri = a,
                    author_id = a_author
                )
                if a_created:
                    created_objects.append(a)
                b_obj, b_created = authorMeta.objects.get_or_create(
                    author_uri = b 
                )
                if b_created:
                    created_objects.append(b)
                a2bRelation.objects.get_or_create(
                    text_a_id = a_obj,
                    person_b_id = b_obj,
                    relation_type = rt
                )
    print("OBJECTS CREATED:")
    for o in created_objects:
        print("-", o)


def check_null(value):
    if value == '':
        return 0
    else:
        return value

def get_annotation_status(value):
    if  value == 'mARkdown' or value =='completed' or value =='inProgress':
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
    
        
def read_csv(filename):
    records= []
    with open(filename,'r',encoding='utf-8') as f:
        
        reader = csv.DictReader(f,fieldnames=['versionUri','date','author_ar','author_lat','book','title_ar','title_lat','ed_info','id','status','tok_length','url','tags','author_from_uri','author_lat_shuhra','author_lat_full_name','char_length'], delimiter='\t')
       
        next(reader)
        for data in reader:
            record = {}
            record['version_uri'] = data['versionUri']
            record['version_lang'] = get_version_lang(record['version_uri'])
            record['date'] = data['date']
            record['author_ar'] = data['author_ar']
            record['author_lat'] = data['author_lat']
            record['text_uri'] = data['book']
            record['title_ar'] = data['title_ar']
            record['title_lat'] = data['title_lat']
            record['ed_info'] = data['ed_info']
            record['version_id'] = data['id']
            record['status'] = data['status']
            record['tok_length'] = check_null(data['tok_length'])
            record['url'] = data['url']
            record['tags'] = data['tags']
            record['author_from_uri'] = data['author_from_uri']
            record['author_lat_shuhra'] = data['author_lat_shuhra']
            record['author_lat_full_name'] = data['author_lat_full_name']
            record['char_length'] = check_null(data['char_length'])
            record['annotation_status'] =  get_annotation_status(data['url'].split('.')[-1])
            if "type" in data:
                record["type"] = data["type"]
            else:
                record["type"] = "book"
            records.append(record)
    return records

def load_records(records):
    print("START LOADING RECORDS")
    for record in records:
        # print(authorMeta.objects.filter(author_uri = "0001AbuTalibCabdManaf").exists()) 
        # never create duplicate author data, except for Anonymous authors:
        print(record['version_uri'])
        author_uri = record['version_uri'].split(".")[0]
        if re.findall('\d{4}Anonymous\.', author_uri):
            create_new = True
        else:
            if not authorMeta.objects.filter(author_uri = author_uri).exists():
                create_new = True
            else:
                create_new = False
        if create_new:
            am,am_created = authorMeta.objects.get_or_create(
            
                author_uri = record['version_uri'].split(".")[0],
                author_ar = record['author_ar'],
                author_ar_norm = normalize_str(record['author_ar']),
                author_lat = record['author_lat'],
                author_lat_norm = normalize_str(record['author_lat']),
                date = record['date'],
                authorDateAH = get_authorDateAH(record['date'], record['type']),
                authorDateCE = get_authorDateCE(record['date'], record['type']),
                authorDateString = str(record['date'])
                )
        else:
            am = authorMeta.objects.filter(author_uri = record['version_uri'].split(".")[0]).first()
            am_created = False

        if not textMeta.objects.filter(text_uri = record['text_uri']).exists():
            item,created = textMeta.objects.get_or_create(
                author_id = am,
                text_uri = record['text_uri'],
                title_ar = record['title_ar'],
                title_ar_norm = normalize_str(record['title_ar']),
                title_lat = record['title_lat'],
                title_lat_norm = normalize_str(record['title_lat']),
                text_type = record["type"],
                tags =  record["tags"]
                )
        else:
            item = textMeta.objects.filter(text_uri = record['text_uri']).first()
        
        versionMeta.objects.get_or_create(
            text_id = item,
            version_id = record['version_id'],
            version_uri = record['version_uri'],
            char_length = record['char_length'],
            tok_length = record['tok_length'],
            url = record['url'],
            ed_info = record['ed_info'],
            tags = record['tags'],
            annotation_status = record['annotation_status'],
            status = record['status'],
            version_lang = record['version_lang']
            )


