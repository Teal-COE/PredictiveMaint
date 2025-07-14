from django.core.management.base import BaseCommand
from predictive.views import train_model1   # or wherever you placed it

class Command(BaseCommand):
    help = 'Auto-trains model for DTVS_festo_current'

    def handle(self, *args, **kwargs):
        train_model1()
