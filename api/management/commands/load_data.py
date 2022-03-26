
import json, csv
from webbrowser import get
from django.db import models
from api.models import authorMeta, textMeta, versionMeta, authorName, AggregatedStats
from django.core.management.base import BaseCommand
import re
import random

import urllib.request


class Command(BaseCommand):
    def handle(self, **options):
        filename = '../OpenITI_Github_clone_metadata_light.txt'
        #filename = 'https://raw.githubusercontent.com/OpenITI/kitab-metadata-automation/master/output/OpenITI_Github_clone_metadata_light.csv'
        
        # with urllib.request.urlopen(filename) as url:
        #     data = url.read().decode('utf-8')
        # #filename = '../test.json'
        
        textMeta.objects.all().delete()
        authorMeta.objects.all().delete()
        versionMeta.objects.all().delete()
        authorName.objects.all().delete()

        read_csv(filename)
        
        #read_json(filename)


def read_json(filename):
    record= {}
    with open(filename,'r') as f:
        for line in f:
            
            data = json.loads(line)
            #print(data)
            record['book_id'] = data['id']
            record['book_uri'] = data['book']
            record['char_length'] = data['char_length']
            record['tok_length'] = data['tok_length']
            record['date'] = data['date']
            record['title_ar'] = data['title_ar']
            record['title_lat'] = data['title_lat']
            record['version_uri'] = data['versionUri']
            record['url'] = data['url']
            record['status'] = data['status'],
            record['author_lat'] = data['author_lat']
            bulk_load(record)

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
        return re.findall("-([a-z]{3})", record['version_uri'])[0]
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
    record= {}
    with open(filename,'r',encoding='utf-8') as f:
        
        reader = csv.DictReader(f,fieldnames=['versionUri','date','author_ar','author_lat','book','title_ar','title_lat','ed_info','id','status','tok_length','url','tags','author_from_uri','author_lat_shuhra','author_lat_full_name','char_length'], delimiter='\t')
       
        next(reader)
        for data in reader:
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
            
            
            # print(authorMeta.objects.filter(author_uri = "0001AbuTalibCabdManaf").exists()) 
            # never create duplicate author data, except for Anonymous authors:

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
                    author_lat = record['author_lat'],
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
                    author_uri = am,
                    text_uri = record['text_uri'],
                    title_ar = record['title_ar'],
                    title_lat = record['title_lat'],
                    text_type = record["type"],
                    tags =  record["tags"]
                    )
            else:
                item = textMeta.objects.filter(text_uri = record['text_uri']).first()
           
            versionMeta.objects.get_or_create(
                text_uri = item,
                version_id = record['version_id'],
                version_uri = record['version_uri'],
                char_length = record['char_length'],
                tok_length = record['tok_length'],
                url = record['url'],
                ed_info = record['ed_info'],
                tags = record['tags'],
                annotation_status = record['annotation_status'],
                status = record['status'],
                language = record['version_lang']
                )
            # name elements are not separately in the metadata file as it is now;
            # loading bogus data for now!
            if am_created:
                for lan in ("ar", "lat"):
                    name_elements = re.split(" *:: *", record['author_'+lan])
                    while len(name_elements) < 5:
                        name_elements.append("")
                    random.shuffle(name_elements)

                    authorName.objects.get_or_create(
                        author_uri = am,
                        language = lan,
                        shuhra = name_elements[0],
                        kunya = name_elements[1],
                        ism = name_elements[2],
                        laqab = name_elements[3],
                        nisba = name_elements[4],
                        )

            

def bulk_load(record):
    #print(record['url'])
    instance = [
        Book(
            book_id = record['book_id'],
            book_uri = record['book_uri'],
            char_length = record['char_length'],
            tok_length = record['tok_length'],
            date = record['date'],
            title_ar = record['title_ar'],
            title_lat = record['title_lat'],
            version_uri = record['version_uri'],
            url = record['url'],
            status = record['status'],
            author_lat = record['author_lat'],
            author_ar = record['author_ar'],
            annotation_status = record['annotation_status']

        )
    ]
    print(instance)
    #Book.objects.bulk_create(instance)

