"""Get a list of all models in the app and the number of objects in it"""

from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = "Show object counts per model"

    def handle(self, *args, **kwargs):
        for model in apps.get_models():
            count = model.objects.count()
            self.stdout.write(f"{model.__name__}: {count}")