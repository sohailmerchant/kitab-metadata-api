import json
from .model import Book

def read_json(filename):
    record= {}
    with open(filename,'r') as f:
        for line in f:
            data = json.loads(line)
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
                       
def bulk_load(record):
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
    Book.objects.bulk_create(instance)

read_json('./OpenITI_Github_clone_metadata_light.json')