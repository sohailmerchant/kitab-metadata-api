
import json
import csv
from webbrowser import get
from django.db import models
from api.models import TextReuseStats, versionMeta
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

        read_csv(filename)


def read_csv(filename):
    record = {}
    with open(filename, 'r', encoding='utf-8') as f:
    
        reader = csv.DictReader(f, delimiter='\t')
        #for data in itertools.islice(reader, 300):
        for data in (reader):
            
            b1 = versionMeta.objects.filter(
                    version_id=data['_T1']).first()
            b2 = versionMeta.objects.filter(
                    version_id=data['_T2']).first()
            
            TextReuseStats.objects.get_or_create(
                book_1 = b1,
                book_2 = b2,
                instances_count=data['instances'],
                book1_word_match=data['WM1_Total'],
                book2_word_match=data['WM2_Total'],
                book1_match_book2_per=data['WM_B1inB2'],
                book2_match_book1_per=data['WM_B2inB1'],
            )
