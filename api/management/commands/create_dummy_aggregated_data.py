
from api.models import Book, AggregatedStats
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, **options):
        #filename = '../OpenITI_Github_clone_metadata_light.txt'
        #filename = '../test.json'
        AggregatedStats.objects.all().delete()
        create_dummy_aggregated_record()
        #read_json(filename)
        
def create_dummy_aggregated_record():
    record = AggregatedStats.objects.create(
    number_of_authors=8030, 
    number_of_unique_authors=5010,
    number_of_books=10110,
    number_of_unique_books=5176)
    record.save()
    print(AggregatedStats.objects.all())