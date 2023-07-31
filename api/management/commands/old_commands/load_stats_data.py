
import json
import csv
from webbrowser import get
from django.db import models
from api.models import TextReuseStats, ReleaseMeta
from django.core.management.base import BaseCommand
import re
import random
import itertools

from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, **options):
        #C:\Users\smerchant\OneDrive\KITAB\Statistical Data\Release\Oct 2022
        filename = '/mnt/c/Users/smerchant/OneDrive/KITAB/Statistical Data/Release/Oct 2022/stats-Oct2022_bi-dir.csv'
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            print(user, superusers)
        exit
        TextReuseStats.objects.all().delete()
        release_code="2022.1.6"

        load_data(filename, release_code)


def load_data(filename, release_code):
    with open(filename, 'r', encoding='utf-8') as f:
    
        reader = csv.DictReader(f, delimiter='\t')
        #for data in itertools.islice(reader, 300):
        for data in reader:
            version_id1 = data['_T1'].split("-")[0].split(".")[0]
            version_id2 = data['_T2'].split("-")[0].split(".")[0]
            b1 = ReleaseMeta.objects.get(
                    release__release_code=release_code,
                    version_meta__version_id=version_id1
                    )
            b2 = ReleaseMeta.objects.get(
                    release__release_code=release_code,
                    version_meta__version_id=version_id2
                    )
            
            TextReuseStats.objects.get_or_create(
                book_1 = b1,
                book_2 = b2,
                instances_count=data['instances'],
                book1_words_matched=data['WM1_Total'],
                book2_words_matched=data['WM2_Total'],
                book1_pct_words_matched=data['WM_B1inB2'],
                book2_pct_words_matched=data['WM_B2inB1'],
            )
