from __future__ import absolute_import, unicode_literals
import shutil
import functools
import os
import subprocess
import logging

from zipfile import is_zipfile, ZipFile

from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER
from celery import shared_task

from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from vavilov3.views import DETAIL, format_error_message
from vavilov3.models import UserTasks, ObservationImage
from vavilov3.entities.accession import create_accession_in_db
from vavilov3.entities.institute import create_institute_in_db
from vavilov3.entities.accessionset import create_accessionset_in_db
from vavilov3.entities.study import create_study_in_db
from vavilov3.entities.observation_variable import create_observation_variable_in_db
from vavilov3.entities.observation_unit import create_observation_unit_in_db
from vavilov3.entities.plant import create_plant_in_db
from vavilov3.entities.observation import create_observation_in_db
from vavilov3.entities.trait import create_trait_in_db
from vavilov3.entities.scale import create_scale_in_db
from vavilov3.entities.observation_image import create_observation_image_in_db
from vavilov3.conf.settings import (LONG_PROCESS_TIMEOUT,
                                    SHORT_PROCESS_TIMEOUT)
from vavilov3.utils import observation_image_cleanup

User = get_user_model()
logger = logging.getLogger('vavilov.prod')


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


def _create_items_task(validated_data, username, func, item_type, conf=None):
    errors = []
    with transaction.atomic():
        user = User.objects.get(username=username) if username else None
        for item in validated_data:
            if conf:
                try:
                    func(item, user, conf)
                except ValueError as error:
                    errors.append(str(error))
            else:
                try:
                    func(item, user)
                except ValueError as error:
                    errors.append(str(error))

        if errors:
            raise ValidationError(format_error_message(errors))
    return {DETAIL: '{} {} added'.format(len(validated_data), item_type)}


@shared_task(time_limit=LONG_PROCESS_TIMEOUT,
             soft_time_limit=LONG_PROCESS_TIMEOUT)
def create_accessions_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_accession_in_db, 'accessions')


@shared_task(time_limit=LONG_PROCESS_TIMEOUT,
             soft_time_limit=LONG_PROCESS_TIMEOUT)
def create_accessionsets_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_accessionset_in_db, 'accessionsets')


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
def create_studies_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_study_in_db, 'studies')


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
def create_observation_variables_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_observation_variable_in_db, 'observation_variables')


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
def create_observation_units_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_observation_unit_in_db,
                              'observation_units')


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
def create_plants_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_plant_in_db, 'plants')


@shared_task(time_limit=LONG_PROCESS_TIMEOUT,
             soft_time_limit=LONG_PROCESS_TIMEOUT)
def create_observations_task(validated_data, username, conf=None):
    return _create_items_task(validated_data, username,
                              create_observation_in_db, 'observations', conf)


@shared_task(time_limit=LONG_PROCESS_TIMEOUT,
             soft_time_limit=LONG_PROCESS_TIMEOUT)
def create_observation_images_task(validated_data, username, conf=None):
    try:
        return _create_items_task(validated_data, username,
                                  create_observation_image_in_db,
                                  'observation_images', conf)
    except ValidationError:
        try:
            observation_image_cleanup(delete=True)
        except Exception as error:
            raise ValidationError(error)
        raise
    finally:
        shutil.rmtree(conf['extraction_dir'])


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
def create_trait_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_trait_in_db, 'traits')


@shared_task
def create_scale_task(validated_data, username):
    return _create_items_task(validated_data, username,
                              create_scale_in_db, 'scales')


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
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


@shared_task
def create_tmp_dir(extracted_dir):
    os.mkdir(extracted_dir)
    subprocess.run(['chmod', '2777', extracted_dir])


def add_task_to_user(user, async_result):
    UserTasks.objects.create(user=user, task_id=async_result.task_id)


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
def extract_files_from_zip(fpath, extract_dir=None):
    if not is_zipfile(fpath):
        raise ValueError('File must be a zip file')
    if extract_dir is not None:
        os.mkdir(extract_dir)

    zip_file = ZipFile(fpath)
    valid_data = []
    for member in zip_file.filelist:
        try:
            # this.method exists strting in python 3.6
            is_dir = member.is_dir()
        except AttributeError:
            is_dir = member.filename.endswith('/')

        if is_dir:
            continue
        directory_tree = member.filename.split('/')
        try:
            study = directory_tree[-2]
            accession = directory_tree[-3]
            institute_code, germplasm_number = accession.split('#', 1)
        except (IndexError, ValueError):
            raise ValueError("The zip file's Directory tree is wrong!")

        image_path = zip_file.extract(member, path=extract_dir)

        valid_data.append({'study': study, INSTITUTE_CODE: institute_code,
                           GERMPLASM_NUMBER: germplasm_number,
                           'image_path': image_path})
    return valid_data


@shared_task(time_limit=SHORT_PROCESS_TIMEOUT,
             soft_time_limit=SHORT_PROCESS_TIMEOUT)
def delete_image(uid):
    try:
        ObservationImage.objects.get(observation_image_uid=uid).delete()
    except ObservationImage.DoesNotExist:
        raise ValidationError('Could not find image')


@shared_task
def wait_func(sec):
    print('start wait')
    import time
    time.sleep(sec)
    print('end wait')
    return {'detail': 'all good'}
