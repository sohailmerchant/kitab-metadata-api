
import json, csv
from django.db import models
from api.models import Book
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, **options):
        filename = '../OpenITI_Github_clone_metadata_light.txt'
        #filename = '../test.json'
        Book.objects.all().delete()
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
            bulk_load(record)

def check_null(value):
    if value == '':
        return 0
    else:
        return value

def read_csv(filename):
    record= {}
    with open(filename,'r',encoding='utf-8') as f:
        reader = csv.DictReader(f,fieldnames=['versionUri','date','author_ar','author_lat','book','title_ar','title_lat','ed_info','id','status','tok_length','url','tags','author_from_uri','author_lat_shuhra','author_lat_full_name','char_length'], delimiter='\t')
        next(reader)
        for data in reader:
            record['version_uri'] = data['versionUri']
            record['date'] = data['date']
            record['author_ar'] = data['author_ar']
            record['author_lat'] = data['author_lat']
            record['book_uri'] = data['book']
            record['title_ar'] = data['title_ar']
            record['title_lat'] = data['title_lat']
            record['ed_info'] = data['ed_info']
            record['book_id'] = data['id']
            record['status'] = data['status']
            record['tok_length'] = check_null(data['tok_length'])
            record['url'] = data['url']
            record['tags'] = data['tags']
            record['author_from_uri'] = data['author_from_uri']
            record['author_lat_shuhra'] = data['author_lat_shuhra']
            record['author_lat_full_name'] = data['author_lat_full_name']
            record['char_length'] = check_null(data['char_length'])
            #print(record['char_length'])
            Book.objects.create(
            book_id = record['book_id'],
            book_uri = record['book_uri'],
            char_length = record['char_length'],
            tok_length = record['tok_length'],
            date = record['date'],
            title_ar = record['title_ar'],
            title_lat = record['title_lat'],
            version_uri = record['version_uri'],
            url = record['url']
            
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
            url = record['url']
        )
    ]
    print(instance)
    #Book.objects.bulk_create(instance)

