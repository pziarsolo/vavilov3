import json

from vavilov3.serializers.institute import create_institute_in_db
from vavilov3.serializers.accession import create_accession_in_db
from vavilov3.models import Group
from vavilov3.serializers.accessionset import create_accessionset_in_db
from vavilov3.views import DETAIL
from vavilov3.serializers.study import serialize_study_from_csv, \
    create_study_in_db


def _load_items_from_file(fpath, kind):
    fhand = open(fpath)
    items = json.load(fhand)

    for item in items:
        if kind == 'institute':
            create_institute_in_db(item)
        elif kind == 'accession':
            create_accession_in_db(item)


def load_institutes_from_file(fpath):
    _load_items_from_file(fpath, 'institute')


def load_accessions_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        group = Group.objects.get(name=item['metadata']['group'])
        del item['metadata']['group']
        is_public = item['metadata'].pop('is_public')
        create_accession_in_db(item, group, is_public)


def load_accessionsets_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        group = Group.objects.get(name=item['metadata']['group'])
        del item['metadata']['group']
        is_public = item['metadata'].pop('is_public')
        create_accessionset_in_db(item, group, is_public)


def load_studies_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        group = Group.objects.get(name=item['metadata']['group'])
        del item['metadata']['group']
        is_public = item['metadata'].pop('is_public')
        create_study_in_db(item, group, is_public)


def assert_error_is_equal(error, error_message):
    assert error[DETAIL] == error_message
