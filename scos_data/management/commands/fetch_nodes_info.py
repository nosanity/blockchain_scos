# coding: utf-8

from django.core.management.base import BaseCommand
from scos_data.models import RawJsonData


class Command(BaseCommand):
    help = u'Периодический сбор данных с нод'

    def handle(self, *args, **options):
        pass
