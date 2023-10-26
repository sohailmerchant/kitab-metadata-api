"""Fix SRT URLs: 

http://dev.kitab-project.org/2023.1.8 
> https://dev.kitab-project.org/2023.1.8-pairwise
http://dev.kitab-project.org/passim01122022-v7
> https://dev.kitab-project.org/2022.2.7-pairwise
http://dev.kitab-project.org/passim01102022
> https://dev.kitab-project.org/2022.1.6-pairwise
http://dev.kitab-project.org/passim01102021
> https://dev.kitab-project.org/2021.2.5-pairwise


"""

from django.db.models import F, Func, Value, TextField
from django.db.models.functions import Replace
from django.core.management.base import BaseCommand

from api.models import TextReuseStats



class Command(BaseCommand):
    def handle(self, **options):
        

        TextReuseStats.objects.update(\
            tsv_url=Replace("tsv_url", 
                            Value("http://dev.kitab-project.org/2023.1.8"), 
                            Value("https://dev.kitab-project.org/2023.1.8-pairwise")))
        TextReuseStats.objects.update(\
                        tsv_url=Replace("tsv_url", 
                            Value("http://dev.kitab-project.org/passim01122022-v7"), 
                            Value("https://dev.kitab-project.org/2022.2.7-pairwise")))
        TextReuseStats.objects.update(\
                        tsv_url=Replace("tsv_url", 
                            Value("http://dev.kitab-project.org/passim01102022"), 
                            Value("https://dev.kitab-project.org/2022.1.6-pairwise")))
        TextReuseStats.objects.update(\
                        tsv_url=Replace("tsv_url", 
                            Value("http://dev.kitab-project.org/passim01102021"), 
                            Value("https://dev.kitab-project.org/2021.2.5-pairwise")))
        