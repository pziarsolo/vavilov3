#
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

from copy import deepcopy
from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError
from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_UNIT_NAME,
                                    OBSERVATION_UNIT_LEVEL,
                                    OBSERVATION_UNIT_REPLICATE,
                                    INSTITUTE_CODE, GERMPLASM_NUMBER, ACCESSION,
                                    OBSERVATION_UNIT_STUDY, PLANTS)
from vavilov3.models import Accession, Study, Plant, ObservationUnit
from vavilov3.permissions import is_user_admin
from vavilov3.id_validator import validate_name


class ObservationUnitValidationError(Exception):
    pass


OBSERVATION_UNIT_ALLOWED_FIELDS = [OBSERVATION_UNIT_NAME,
                                   ACCESSION, OBSERVATION_UNIT_LEVEL,
                                   OBSERVATION_UNIT_REPLICATE,
                                   OBSERVATION_UNIT_STUDY, PLANTS]


def validate_observation_unit_data(data):
    if OBSERVATION_UNIT_NAME not in data:
        raise ObservationUnitValidationError('{} mandatory'.format(OBSERVATION_UNIT_NAME))
    if ACCESSION not in data:
        raise ObservationUnitValidationError('{} mandatory'.format(ACCESSION))
    else:
        if INSTITUTE_CODE not in data[ACCESSION]:
            raise ObservationUnitValidationError('{} mandatory in accession'.format(INSTITUTE_CODE))
        if GERMPLASM_NUMBER not in data[ACCESSION]:
            raise ObservationUnitValidationError('{} mandatory in accession'.format(GERMPLASM_NUMBER))

    if OBSERVATION_UNIT_LEVEL not in data:
        raise ObservationUnitValidationError('{} mandatory'.format(OBSERVATION_UNIT_LEVEL))
    if OBSERVATION_UNIT_REPLICATE not in data:
        raise ObservationUnitValidationError('{} mandatory'.format(OBSERVATION_UNIT_REPLICATE))
    if OBSERVATION_UNIT_STUDY not in data:
        raise ObservationUnitValidationError('{} mandatory'.format(OBSERVATION_UNIT_STUDY))

    not_allowed_fields = set(data.keys()).difference(OBSERVATION_UNIT_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise ObservationUnitValidationError(msg)
    try:
        validate_name(data[OBSERVATION_UNIT_NAME])
    except ValueError as msg:
        raise ObservationUnitValidationError(msg)


class ObservationUnitStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._metadata = Metadata()

        elif api_data:
            payload = deepcopy(api_data['data'])
            self._data = payload
            self._metadata = Metadata(api_data['metadata'])

        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        return _data

    def get_api_document(self):
        return {'data': self.data,
                'metadata': self.metadata.data}

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    @property
    def name(self):
        return self._data[OBSERVATION_UNIT_NAME]

    @name.setter
    def name(self, name):
        self._data[OBSERVATION_UNIT_NAME] = name

    @property
    def accession(self):
        return self._data.get(ACCESSION, None)

    @accession.setter
    def accession(self, accession):
        assert not set(accession.keys()).difference(set([INSTITUTE_CODE, GERMPLASM_NUMBER]))
        self._data[ACCESSION] = accession

    @property
    def level(self):
        return self._data.get(OBSERVATION_UNIT_LEVEL, None)

    @level.setter
    def level(self, level):
        self._data[OBSERVATION_UNIT_LEVEL] = level

    @property
    def replicate(self):
        return self._data.get(OBSERVATION_UNIT_REPLICATE, None)

    @replicate.setter
    def replicate(self, replicate: str):
        if replicate:
            self._data[OBSERVATION_UNIT_REPLICATE] = replicate

    @property
    def study(self) -> str:
        return self._data.get(OBSERVATION_UNIT_STUDY, None)

    @study.setter
    def study(self, study: str):
        if study:
            self._data[OBSERVATION_UNIT_STUDY] = study

    @property
    def plants(self):
        return self._data.get(PLANTS, None)

    @plants.setter
    def plants(self, plants):
        if plants:
            self._data[PLANTS] = plants

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.study.group.name
        accepted_fields = OBSERVATION_UNIT_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if (fields is None or OBSERVATION_UNIT_NAME in fields) and instance is not None:
            self.name = instance.name
        if (fields is None or ACCESSION in fields) and instance.accession is not None:
            self.accession = {INSTITUTE_CODE: instance.accession.institute.code,
                              GERMPLASM_NUMBER: instance.accession.germplasm_number}
        if (fields is None or OBSERVATION_UNIT_LEVEL in fields) and instance.level:
            self.level = instance.level
        if (fields is None or OBSERVATION_UNIT_REPLICATE in fields) and instance.replicate is not None:
            self.replicate = instance.replicate
        if (fields is None or OBSERVATION_UNIT_STUDY in fields) and instance.study is not None:
            self.study = instance.study.name
        if (fields is None or PLANTS in fields) and instance.plant_set is not None:
            self.plants = instance.plant_set.values_list('name', flat=True)

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = OBSERVATION_UNIT_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

    def populate_from_csvrow(self, row):

        for field, value in row.items():
            if not value:
                continue
            field_conf = OBSERVATION_UNIT_CSV_FIELD_CONFS.get(field)

            if field_conf:
                setter = field_conf['setter']
                setter(self, value)


def process_accession(obj, value):
    try:
        institute_code, number = value.split(':', 1)

    except IndexError:
        msg = 'Accession field should be a string with institute code'
        msg += ' and germplasm number seprated by a :'
        raise ValidationError(msg)

    obj.accession = {INSTITUTE_CODE: institute_code.strip(),
                     GERMPLASM_NUMBER: number.strip()}


_OBSERVATION_UNIT_CSV_FIELD_CONFS = [
    {'csv_field_name': 'NAME', 'getter': lambda x: x.name,
     'setter': lambda obj, val: setattr(obj, 'name', val)},
    {'csv_field_name': 'ACCESSION', 'getter': lambda x: x.accession,
     'setter': process_accession},
    {'csv_field_name': 'LEVEL', 'getter': lambda x: x.level,
     'setter': lambda obj, val: setattr(obj, 'level', val)},
    {'csv_field_name': 'REPLICATE', 'getter': lambda x: x.replicate,
     'setter': lambda obj, val: setattr(obj, 'replicate', val)},
    {'csv_field_name': 'STUDY_NAME', 'getter': lambda x: x.study,
     'setter': lambda obj, val: setattr(obj, 'study', val)},
    {'csv_field_name': 'PLANTS', 'getter': lambda x: x.plants,
     'setter': lambda obj, val: setattr(obj, 'plants', val.split(':') if val else None)},
]
OBSERVATION_UNIT_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _OBSERVATION_UNIT_CSV_FIELD_CONFS])


def create_observation_unit_in_db(api_data, user=None):
    try:
        struct = ObservationUnitStruct(api_data)
    except ObservationUnitValidationError as error:
        print(error)
        raise

    if struct.metadata.group:
        msg = 'can not set group while creating the observation unit'
        raise ValueError(msg)
    try:
        study = Study.objects.get(name=struct.study)
    except Study.DoesNotExist:
        msg = 'The study has not been added yet to the database: ' + struct.study
        raise ValueError(msg)
    institute_code = struct.accession[INSTITUTE_CODE]
    germplasm_number = struct.accession[GERMPLASM_NUMBER]
    try:
        accession = Accession.objects.get(institute__code=institute_code,
                                          germplasm_number=germplasm_number)
    except Accession.DoesNotExist:
        msg = 'The given accessoin is not in db: {} {}'.format(institute_code,
                                                               germplasm_number)
        raise ValueError(msg)
    study_belongs_to_user = bool(user.groups.filter(name=study.group.name).count())

    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not add observation unit to a study you dont own: {}'
        msg = msg.format(study.group.name)
        raise ValueError(msg)

    with transaction.atomic():
        try:
            observation_unit = ObservationUnit.objects.create(
                name=struct.name,
                accession=accession,
                level=struct.level,
                replicate=struct.replicate,
                study=study)
        except IntegrityError:
            msg = 'This observation unit already exists in db: {}'.format(struct.name)
            raise ValueError(msg)
        if struct.plants:
            _add_plants_to_observation_unit(struct.plants, user, observation_unit)

    return observation_unit


def _add_plants_to_observation_unit(plants, user, observation_unit):
    for plant in plants:
        try:
            plant = Plant.objects.get(name=plant)
            plant_belongs_to_user = bool(user.groups.filter(name=plant.group.name).count())
            if not plant_belongs_to_user and not is_user_admin(user):
                msg = 'Can not add plant you dont own to observation unit: {}'
                msg = msg.format(plant.name)
                raise ValueError(msg)
        except Plant.DoesNotExist:
            msg = 'The given plant does not exist in {} : {}'
            raise ValueError(msg.format(observation_unit.name, plant))
        observation_unit.plant_set.add(plant)


def update_observation_unit_in_db(validated_data, instance, user):
    struct = ObservationUnitStruct(api_data=validated_data)
    if struct.name != instance.name:
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))
    try:
        study = Study.objects.get(name=struct.study)
    except Study.DoesNotExist:
        msg = 'The study has not been added yet to the database: ' + struct.study
        raise ValueError(msg)
    institute_code = struct.accession[INSTITUTE_CODE]
    germplasm_number = struct.accession[GERMPLASM_NUMBER]

    try:
        accession = Accession.objects.get(institute__code=institute_code,
                                          germplasm_number=germplasm_number)
    except Accession.DoesNotExist:
        msg = 'The given accessoin is not in db: {} {}'.format(institute_code,
                                                               germplasm_number)
        raise ValueError(msg)

    study_belongs_to_user = bool(user.groups.filter(name=study.group.name).count())

    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not change ownership if study does not belong to you : {}'
        msg = msg.format(study.group.name)
        raise ValidationError(format_error_message(msg))

    instance.accession = accession
    instance.level = struct.level
    instance.replicate = struct.replicate
    instance.study = study

    instance.save()
    plants = [] if struct.plants is None else struct.plants

    instance.plant_set.clear()
    _add_plants_to_observation_unit(plants, user, instance)

    return instance
