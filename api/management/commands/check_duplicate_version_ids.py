import json, csv
from webbrowser import get
from django.db import models
from api.models import authorMeta, textMeta, versionMeta, personName, AggregatedStats
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re
import random

class Command(BaseCommand):
    def handle(self, **options):
        filename = 'OpenITI_Github_clone_metadata_light.csv'
        fp  = os.path.join(settings.BASE_DIR, filename)
        with open(fp, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f,fieldnames=['versionUri','date','author_ar','author_lat','book','title_ar','title_lat','ed_info','id','status','tok_length','url','tags','author_from_uri','author_lat_shuhra','author_lat_full_name','char_length'], delimiter='\t')
       
            next(reader)
            version_ids = dict()
            for row in reader:
                if not row["id"] in version_ids:
                    version_ids[row["id"]] = [row["versionUri"]]
                else:
                    version_ids[row["id"]].append(row["versionUri"])
                    print("DUPLICATE:", version_ids[row["id"]])
        # with open(fp, mode="r", encoding="utf-8") as f:
        #     data = f.read()
        #     for version_id in version_ids:
        #         if len(version_ids[version_id]) > 1:
        #             for i, row in enumerate(re.findall(".+"+version_id+".+", data)):
        #                 print(i, row)
        #                 new_id = version_id+str(i)
        #                 if new_id in version_ids:
        #                     print("PROBLEM: NEW_ID ALREADY IN VERSION_IDS:", new_id)
        #                 new_row = re.sub(version_id, new_id, row)
        #                 data = re.sub(row, new_row, data)
        # with open(fp, mode="w", encoding="utf-8") as f:
        #     f.write(data)



        
                