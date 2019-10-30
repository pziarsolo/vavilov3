# Copyright (C) 2019 P.Ziarsolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import pytz
import uuid
import hashlib

from copy import deepcopy
from collections import OrderedDict
from datetime import datetime

from django.conf.global_settings import TIME_ZONE
from django.db import transaction
from django.db.utils import IntegrityError
from django.core.files.base import File

from rest_framework.exceptions import ValidationError

from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_UNIT,
                                    OBSERVATION_CREATION_TIME, OBSERVER,
                                    INSTITUTE_CODE, GERMPLASM_NUMBER,
                                    OBSERVATION_STUDY, ACCESSION, IMAGE,
                                    OBSERVATION_IMAGE_UID, IMAGE_SMALL,
                                    IMAGE_MEDIUM, IMAGE_FPATH)
from vavilov3.conf.settings import DATETIME_FORMAT
from vavilov3.models import ObservationUnit, Study, Accession, ObservationImage
from vavilov3.permissions import is_user_admin


class ObservationImageValidationError(Exception):
    pass


TRAITS_IN_COLUMNS = 'traits_in_columns'
CREATE_OBSERVATION_UNITS = 'create_observation_units'

OBSERVATION_ALLOWED_FIELDS = [OBSERVATION_IMAGE_UID, OBSERVATION_UNIT,
                              OBSERVATION_CREATION_TIME, OBSERVER,
                              OBSERVATION_STUDY, ACCESSION, IMAGE, IMAGE_MEDIUM,
                              IMAGE_SMALL, INSTITUTE_CODE, GERMPLASM_NUMBER,
                              IMAGE_FPATH]


def validate_observation_image_data(data, conf=None):
    if conf is None:
        conf = {}
    create_observation_units = True  # conf.get(CREATE_OBSERVATION_UNITS, None)
    if OBSERVATION_UNIT not in data and not create_observation_units:
        raise ObservationImageValidationError('{} mandatory'.format(OBSERVATION_UNIT))

    if (OBSERVATION_UNIT not in data and create_observation_units and
            OBSERVATION_STUDY not in data):
        raise ObservationImageValidationError('{} mandatory'.format(OBSERVATION_STUDY))

    if (OBSERVATION_UNIT not in data and create_observation_units and
            (GERMPLASM_NUMBER not in data or INSTITUTE_CODE not in data)):
        raise ObservationImageValidationError('GermplasmNumber and InstituteCode mandatory')

    if IMAGE not in data and IMAGE_FPATH not in data:
        raise ObservationImageValidationError('image or image_fpath mandatory'.format(IMAGE))

    not_allowed_fields = set(data.keys()).difference(OBSERVATION_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise ObservationImageValidationError(msg)


class ObservationImageStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}

        elif api_data:
            if GERMPLASM_NUMBER in api_data and INSTITUTE_CODE in api_data:
                api_data[ACCESSION] = {GERMPLASM_NUMBER: api_data.pop(GERMPLASM_NUMBER),
                                       INSTITUTE_CODE: api_data.pop(INSTITUTE_CODE)}
            payload = api_data
            self._data = payload

        elif instance:
            self._data = {}
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        return _data

    def get_api_document(self):
        return self.data

    @property
    def observation_image_uid(self):
        return self._data.get(OBSERVATION_IMAGE_UID, None)

    @observation_image_uid.setter
    def observation_image_uid(self, uid):
        self._data[OBSERVATION_IMAGE_UID] = uid

    @property
    def observation_unit(self):
        return self._data.get(OBSERVATION_UNIT, None)

    @observation_unit.setter
    def observation_unit(self, observation_unit):
        self._data[OBSERVATION_UNIT] = observation_unit

    @property
    def creation_time(self):
        return self._data.get(OBSERVATION_CREATION_TIME, None)

    @creation_time.setter
    def creation_time(self, creation_time):
        self._data[OBSERVATION_CREATION_TIME] = creation_time

    @property
    def observer(self):
        return self._data.get(OBSERVER, None)

    @observer.setter
    def observer(self, observer: str):
        if observer:
            self._data[OBSERVER] = observer

    @property
    def image(self):
        return self._data.get(IMAGE, None)

    @image.setter
    def image(self, image):
        if image:
            self._data[IMAGE] = image

    @property
    def image_small(self):
        return self._data.get(IMAGE_SMALL, None)

    @image_small.setter
    def image_small(self, image_small):
        if image_small:
            self._data[IMAGE_SMALL] = image_small

    @property
    def image_medium(self):
        return self._data.get(IMAGE_MEDIUM, None)

    @image_medium.setter
    def image_medium(self, image_medium):
        if image_medium:
            self._data[IMAGE_MEDIUM] = image_medium

    @property
    def accession(self) -> str:
        return self._data.get(ACCESSION, None)

    @accession.setter
    def accession(self, accession: str):
        if accession:
            self._data[ACCESSION] = accession

    @property
    def study(self) -> str:
        return self._data.get(OBSERVATION_STUDY, None)

    @study.setter
    def study(self, study: str):
        if study:
            self._data[OBSERVATION_STUDY] = study

    def _populate_with_instance(self, instance, fields):
        accepted_fields = OBSERVATION_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if ((fields is None or OBSERVATION_IMAGE_UID in fields) and
                instance.observation_image_uid is not None):
            self.observation_image_uid = instance.observation_image_uid

        if ((fields is None or OBSERVATION_UNIT in fields) and
                instance.observation_unit is not None):
            self.observation_unit = instance.observation_unit.name
        if (fields is None or IMAGE in fields) and instance.image is not None:
            self.image = instance.image.url
        if (fields is None or IMAGE_MEDIUM in fields) and instance.image_medium is not None:
            self.image_medium = instance.image_medium.url
        if (fields is None or IMAGE_SMALL in fields) and instance.image_small is not None:
            self.image_small = instance.image_small.url
        if (fields is None or OBSERVER in fields) and instance.observer is not None:
            self.observer = instance.observer
        if ((fields is None or OBSERVATION_CREATION_TIME in fields) and
                instance.creation_time is not None):
            self.creation_time = instance.creation_time.strftime(DATETIME_FORMAT)

        if ((fields is None or OBSERVATION_STUDY in fields) and
                instance.observation_unit is not None and
                instance.observation_unit.study is not None):
            self.study = instance.observation_unit.study.name
        if ((fields is None or ACCESSION in fields) and
                instance.observation_unit is not None and
                instance.observation_unit.accession is not None):
            self.accession = {INSTITUTE_CODE: instance.observation_unit.accession.institute.code,
                              GERMPLASM_NUMBER: instance.observation_unit.accession.germplasm_number}

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = OBSERVATION_VARIABLE_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

    def populate_from_csvrow(self, row):

        for field, value in row.items():
            if not value:
                continue
            field_conf = OBSERVATION_VARIABLE_CSV_FIELD_CONFS.get(field)

            if field_conf:
                setter = field_conf['setter']
                setter(self, value)


_OBSERVATION_VARIABLE_CSV_FIELD_CONFS = [
    {'csv_field_name': 'OBSERVATION_ID', 'getter': lambda x: x.observation_id,
     'setter': lambda obj, val: setattr(obj, 'observation_id', val)},
    {'csv_field_name': 'OBSERVATION_VARIABLE', 'getter': lambda x: x.observation_variable,
     'setter': lambda obj, val: setattr(obj, 'observation_variable', val)},
    {'csv_field_name': 'OBSERVATION_UNIT', 'getter': lambda x: x.observation_unit,
     'setter': lambda obj, val: setattr(obj, 'observation_unit', val)},
    {'csv_field_name': 'CREATION_TIME', 'getter': lambda x: x.creation_time,
     'setter': lambda obj, val: setattr(obj, 'creation_time', val)},
    {'csv_field_name': 'OBSERVER', 'getter': lambda x: x.observer,
     'setter': lambda obj, val: setattr(obj, 'observer', val)},
    {'csv_field_name': 'VALUE', 'getter': lambda x: x.value,
     'setter': lambda obj, val: setattr(obj, 'value', val)},
    {'csv_field_name': 'VALUE_BEAUTY', 'getter': lambda x: x.beauty_value,
     'setter': lambda obj, val: setattr(obj, 'beauty_value', val)},
    {'csv_field_name': 'STUDY', 'getter': lambda x: x.study,
     'setter': lambda obj, val: setattr(obj, 'study', val)},
    {'csv_field_name': 'ACCESSION',
     'getter': lambda x: '{}:{}'.format(x.accession[INSTITUTE_CODE],
                                        x.accession[GERMPLASM_NUMBER]),
     'setter': lambda obj, val: setattr(obj, 'accession', val)},
]
OBSERVATION_VARIABLE_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _OBSERVATION_VARIABLE_CSV_FIELD_CONFS])


def _get_or_create_observation_unit(struct, create_observation_unit):
    if not create_observation_unit and not struct.observation_unit:
        msg = 'No observation unit provided'
        raise ValueError(msg)
    elif struct.observation_unit:
        try:
            observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
        except ObservationUnit.DoesNotExist:
            msg = 'This observation Unit {} does not exist in db'
            msg = msg.format(struct.observation_unit)
            raise ValueError(msg)
    elif not struct.observation_unit and create_observation_unit == 'foreach_observation':
        try:
            study = Study.objects.get(name=struct.study)
        except Study.DoesNotExist:
            msg = 'Not able to get or create an observation unit with the given conf'
            msg += ' {} study not found'
            raise ValueError(msg.format(struct.study))
        try:
            accession = Accession.objects.get(germplasm_number=struct.accession[GERMPLASM_NUMBER],
                                              institute__code=struct.accession[INSTITUTE_CODE])
        except Accession.DoesNotExist:
            msg = 'Not able to get or create an observation unit with the given conf '
            msg += '{} accession not found'
            raise ValueError(msg.format(struct.accession[GERMPLASM_NUMBER]))

        random_name = uuid.uuid4()
        observation_unit = ObservationUnit.objects.create(study=study,
                                                          accession=accession,
                                                          level='whole plant',
                                                          name=random_name)
    else:
        msg = 'Not able to get or create an observation unit with the given conf'
        raise ValueError(msg)
    return observation_unit


def get_datetime_from_strdate(str_date):
    if not str_date:
        return None
    datetime.strftime(str_date, "")


def create_observation_image_in_db(api_data, user, conf=None):
    if IMAGE_FPATH in api_data and IMAGE not in api_data:
        api_data[IMAGE] = File(open(api_data.pop(IMAGE_FPATH), mode='rb'))

    if conf is None:
        conf = {}
    create_observation_unit = conf.get(CREATE_OBSERVATION_UNITS, None)
    try:
        struct = ObservationImageStruct(api_data)
    except ObservationImageValidationError as error:
        print('a', error)
        raise

    uid = hashlib.sha256(struct.image.read()).hexdigest()
    struct.image.seek(0)

    if struct.creation_time:
        timezone = pytz.timezone(TIME_ZONE)
        creation_time = timezone.localize(datetime.strptime(struct.creation_time,
                                                            DATETIME_FORMAT))
    else:
        creation_time = None

    with transaction.atomic():
        observation_unit = _get_or_create_observation_unit(struct, create_observation_unit)
        study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())

        if not study_belongs_to_user and not is_user_admin(user):
            msg = 'Can not add observation unit to a study you dont own: {}'
            msg = msg.format(observation_unit.study.group.name)
            raise ValueError(msg)

        try:
            ObservationImage.objects.get(observation_image_uid=uid)
            msg = 'This image already exists in db: study {}, accession {}, uid, {}'
            msg += msg.format(struct.study, struct.accession, uid)
            raise ValueError(msg)
        except ObservationImage.DoesNotExist:
            pass

        try:
            observation = ObservationImage.objects.create(
                observation_image_uid=uid,
                observation_unit=observation_unit,
                image=api_data['image'],
                observer=struct.observer,
                creation_time=creation_time)
        except IntegrityError as error:
            if 'duplicate key value' in str(error):
                msg = 'This image already exists in db: {}'.format(uid)
                raise ValueError(msg)
            raise ValueError(str(error))
        except PermissionError as error:
            raise ValueError(str(error))
        except Exception as error:
            raise ValueError(str(error))

    return observation

# def update_observation_in_db(validated_data, instance, user):
#     struct = ObservationStruct(api_data=validated_data)
#     if struct.observation_id != instance.observation_id:
#         msg = 'Can not change id in an update operation'
#         raise ValidationError(format_error_message(msg))
#     try:
#         observation_variable = ObservationVariable.objects.get(name=struct.observation_variable)
#     except ObservationVariable.DoesNotExist:
#         msg = 'Observation variable {} does not exist in db'
#         msg = msg.format(struct.observation_variable)
#         raise ValueError(msg)
#     try:
#         observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
#     except ObservationUnit.DoesNotExist:
#         msg = 'Observation unit {} does not exist in db'
#         msg = msg.format(struct.observation_unit)
#         raise ValueError(msg)
#
#     study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())
#     if not study_belongs_to_user and not is_user_admin(user):
#         msg = 'Can not change observation unit because this is in a study you dont own: {}'
#         msg = msg.format(observation_unit.study.name)
#         raise ValueError(msg)
#
#     if struct.creation_time:
#         timezone = pytz.timezone(TIME_ZONE)
#         creation_time = timezone.localize(datetime.strptime(struct.creation_time,
#                                                             DATETIME_FORMAT))
#     else:
#         creation_time = None
#
#     instance.observation_variable = observation_variable
#     instance.observation_unit = observation_unit
#     instance.value = struct.value
#     instance.observer = struct.observer
#     instance.creation_time = creation_time
#
#     instance.save()
#     return instance
