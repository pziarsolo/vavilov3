import json

from django.contrib.auth import get_user_model

from vavilov3.serializers.institute import create_institute_in_db
from vavilov3.serializers.accession import create_accession_in_db
from vavilov3.models import Group, Study
from vavilov3.serializers.accessionset import create_accessionset_in_db
from vavilov3.views import DETAIL
from vavilov3.serializers.study import create_study_in_db
from vavilov3.serializers.observation_variable import create_observation_variable_in_db
from vavilov3.serializers.observation_unit import create_observation_unit_in_db
from vavilov3.entities.tags import OBSERVATION_UNIT_STUDY
from vavilov3.serializers.plant import create_plant_in_db
from vavilov3.serializers.observation import create_observation_in_db
from vavilov3.entities.scale import create_scale_in_db
from vavilov3.entities.trait import create_trait_in_db, parse_obo, \
    transform_to_trait_entity_format

User = get_user_model()


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
        user = group.users.first()
        create_accession_in_db(item, user, is_public)


def load_accessionsets_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        group = Group.objects.get(name=item['metadata']['group'])
        del item['metadata']['group']
        is_public = item['metadata'].pop('is_public')
        user = group.users.first()
        create_accessionset_in_db(item, user, is_public)


def load_studies_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        group = Group.objects.get(name=item['metadata']['group'])
        del item['metadata']['group']
        user = group.users.first()
        is_public = item['metadata'].pop('is_public')
        create_study_in_db(item, user, is_public)


def load_observation_variables_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        group = Group.objects.get(name=item['metadata']['group'])
        del item['metadata']['group']
        user = group.users.first()
        create_observation_variable_in_db(item, user)


def load_scales_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        user = User.objects.get(username='admin')
        create_scale_in_db(item, user)


def load_observation_unit_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        study = Study.objects.get(name=item['data'][OBSERVATION_UNIT_STUDY])
        group = study.group
        user = group.users.first()
        create_observation_unit_in_db(item, user)


def load_plants_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        group = Group.objects.get(name=item['metadata']['group'])
        del item['metadata']['group']
        user = group.users.first()
        create_plant_in_db(item, user)


def load_observations_from_file(fpath, obs_group, user=None):
    fhand = open(fpath)
    items = json.load(fhand)
    items = items[obs_group]
    for item in items:
        create_observation_in_db(item, user)


def load_traits_from_file(fpath):
    fhand = open(fpath)
    items = json.load(fhand)
    for item in items:
        user = User.objects.get(username='admin')
        create_trait_in_db(item, user)


def load_traits_from_obo_file(obo_fpath):
    ontology = parse_obo(open(obo_fpath))
    traits = transform_to_trait_entity_format(ontology)
    for item in traits:
        user = User.objects.get(username='admin')
        create_trait_in_db(item, user)


def assert_error_is_equal(error, error_message):
    assert error[DETAIL] == error_message, '{} != {}'.format(error[DETAIL],
                                                             error_message)
