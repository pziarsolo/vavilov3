from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from vavilov3.views import DETAIL
from vavilov3.models import UserTasks
from vavilov3.entities.accession import create_accession_in_db
from vavilov3.entities.institute import create_institute_in_db
from vavilov3.entities.accessionset import create_accessionset_in_db
from vavilov3.entities.study import create_study_in_db
from vavilov3.entities.observation_variable import create_observation_variable_in_db
from vavilov3.entities.observation_unit import create_observation_unit_in_db
from vavilov3.entities.plant import create_plant_in_db
from vavilov3.entities.observation import create_observation_in_db
import functools
from vavilov3.entities.trait import create_trait_in_db
from vavilov3.entities.scale import create_scale_in_db

User = get_user_model()


def add_user_to_task(user):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            async_result = func(*args, **kwargs)
            print('inside_decorator', dir(async_result))
            print('user', user)
            add_task_to_user(user, async_result)
            return async_result

        return wrapper

    return decorator


def _create_items_task(validated_data, username, func, item_type):
    errors = []
    with transaction.atomic():
        user = User.objects.get(username=username) if username else None
        for item in validated_data:
            try:
                func(item, user)
            except ValueError as error:
                errors.append(str(error))

        if errors:
            raise ValidationError(errors)
    return {DETAIL: '{} {} added'.format(len(validated_data), item_type)}


@shared_task
def create_accessions_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_accession_in_db, 'accessions')


@shared_task
def create_accessionsets_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_accessionset_in_db, 'accessionsets')


@shared_task
def create_studies_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_study_in_db, 'studies')


@shared_task
def create_observation_variables_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_observation_variable_in_db, 'observation_variables')


@shared_task
def create_observation_units_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_observation_unit_in_db,
                              'observation_units')


@shared_task
def create_plants_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_plant_in_db, 'plants')


@shared_task
def create_observations_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_observation_in_db, 'observations')


@shared_task
def create_trait_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_trait_in_db, 'traits')


@shared_task
def create_scale_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_scale_in_db, 'scales')


@shared_task
def create_institutes_task(validated_data):
    errors = []
    with transaction.atomic():
        for item in validated_data:
            try:
                create_institute_in_db(item)
            except ValueError as error:
                errors.append(str(error))
        if errors:
            raise ValidationError(errors)

    return {DETAIL: '{} institutes added'.format(len(validated_data))}


def add_task_to_user(user, async_result):
    UserTasks.objects.create(user=user, task_id=async_result.task_id)


@shared_task
def wait_func(sec):
    print('start wait')
    import time
    time.sleep(sec)
    print('end wait')
    return {'detail': 'all good'}
