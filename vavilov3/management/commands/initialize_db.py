import argparse

from django.core.management.base import BaseCommand
from vavilov3.data_io import initialize_db


class Command(BaseCommand):
    help = 'Initialize database'

    def add_arguments(self, parser):
        parser.add_argument('-u', '--users', type=argparse.FileType('r'))

    def handle(self, *arg, **options):
        users_fhand = options['users']
        initialize_db(users_fhand)
