import json

from vavilov3_accession.serializers.institute import create_institute_in_db
from vavilov3_accession.serializers.accession import create_accession_in_db
from vavilov3_accession.models import Group


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
