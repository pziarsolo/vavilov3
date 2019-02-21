import pytz

from copy import deepcopy
from collections import OrderedDict
from datetime import datetime

from django.conf.global_settings import TIME_ZONE
from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_VARIABLE, OBSERVATION_UNIT,
                                    OBSERVATION_CREATION_TIME, OBSERVER, VALUE,
                                    INSTITUTE_CODE, GERMPLASM_NUMBER,
                                    OBSERVATION_STUDY, ACCESSION,
                                    OBSERVATION_ID)
from vavilov3.conf.settings import DATETIME_FORMAT
from vavilov3.models import ObservationUnit, ObservationVariable, Observation
from vavilov3.permissions import is_user_admin


class ObservationValidationError(Exception):
    pass


OBSERVATION_ALLOWED_FIELDS = [OBSERVATION_ID, OBSERVATION_VARIABLE, OBSERVATION_UNIT,
                              OBSERVATION_CREATION_TIME, OBSERVER, VALUE,
                              OBSERVATION_STUDY, ACCESSION]


def validate_observation_data(data):
    if OBSERVATION_VARIABLE not in data:
        raise ObservationValidationError('{} mandatory'.format(OBSERVATION_VARIABLE))
    if OBSERVATION_UNIT not in data:
        raise ObservationValidationError('{} mandatory'.format(OBSERVATION_UNIT))
    if VALUE not in data:
        raise ObservationValidationError('{} mandatory'.format(VALUE))

    not_allowed_fields = set(data.keys()).difference(OBSERVATION_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise ObservationValidationError(msg)


class ObservationStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}

        elif api_data:
            payload = deepcopy(api_data)
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
    def observation_id(self):
        return self._data.get(OBSERVATION_ID, None)

    @observation_id.setter
    def observation_id(self, observation_id):
        self._data[OBSERVATION_ID] = observation_id

    @property
    def observation_variable(self):
        return self._data.get(OBSERVATION_VARIABLE, None)

    @observation_variable.setter
    def observation_variable(self, observation_variable):
        self._data[OBSERVATION_VARIABLE] = observation_variable

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
    def value(self) -> str:
        return self._data.get(VALUE, None)

    @value.setter
    def value(self, value: str):
        if value:
            self._data[VALUE] = value

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

        if ((fields is None or OBSERVATION_ID in fields) and
                instance.observation_id is not None):
            self.observation_id = instance.observation_id
        if ((fields is None or OBSERVATION_VARIABLE in fields) and
                instance.observation_unit is not None):
            self.observation_variable = instance.observation_variable.name
        if ((fields is None or OBSERVATION_UNIT in fields) and
                instance.observation_unit is not None):
            self.observation_unit = instance.observation_unit.name
        if (fields is None or VALUE in fields) and instance.value is not None:
            self.value = instance.value
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
    {'csv_field_name': 'STUDY', 'getter': lambda x: x.study,
     'setter': lambda obj, val: setattr(obj, 'study', val)},
    {'csv_field_name': 'ACCESSION',
     'getter': lambda x: '{}:{}'.format(x.accession[INSTITUTE_CODE],
                                        x.accession[GERMPLASM_NUMBER]),
     'setter': lambda obj, val: setattr(obj, 'accession', val)},
]
OBSERVATION_VARIABLE_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _OBSERVATION_VARIABLE_CSV_FIELD_CONFS])


def _get_or_create_observation_unit(struct):
    try:
        observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
    except ObservationUnit.DoesNotExist:
        msg = 'This observation Unit {} does not exist in db'
        msg = msg.format(struct.observation_unit)
        raise ValueError(msg)
    return observation_unit


def get_datetime_from_strdate(str_date):
    if not str_date:
        return None
    datetime.strftime(str_date, "")


def create_observation_in_db(api_data, user):
    try:
        struct = ObservationStruct(api_data)
    except ObservationValidationError as error:
        print(error)
        raise
    try:
        observation_variable = ObservationVariable.objects.get(name=struct.observation_variable)
    except ObservationVariable.DoesNotExist:
        msg = 'Observation variable {} does not exist in db'
        msg = msg.format(struct.observation_variable)
        raise ValueError(msg)

    observation_unit = _get_or_create_observation_unit(struct)
    study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())

    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not add observation unit to a study you dont own: {}'
        msg = msg.format(observation_unit.study.group.name)
        raise ValueError(msg)
    if struct.creation_time:
        timezone = pytz.timezone(TIME_ZONE)
        creation_time = timezone.localize(datetime.strptime(struct.creation_time,
                                                            DATETIME_FORMAT))
    else:
        creation_time = None

    with transaction.atomic():
        try:
            observation = Observation.objects.create(
                observation_variable=observation_variable,
                observation_unit=observation_unit,
                value=struct.value,
                observer=struct.observer,
                creation_time=creation_time)
        except IntegrityError:
            msg = 'This observation variable already exists in db: {}'.format(struct.observation_id)
            raise ValueError(msg)

    return observation


def update_observation_in_db(validated_data, instance, user):
    struct = ObservationStruct(api_data=validated_data)
    if struct.observation_id != instance.observation_id:
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))
    try:
        observation_variable = ObservationVariable.objects.get(name=struct.observation_variable)
    except ObservationVariable.DoesNotExist:
        msg = 'Observation variable {} does not exist in db'
        msg = msg.format(struct.observation_variable)
        raise ValueError(msg)
    try:
        observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
    except ObservationUnit.DoesNotExist:
        msg = 'Observation unit {} does not exist in db'
        msg = msg.format(struct.observation_unit)
        raise ValueError(msg)

    study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())
    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not change observation unit because this is in a study you dont own: {}'
        msg = msg.format(observation_unit.study.name)
        raise ValueError(msg)

    if struct.creation_time:
        timezone = pytz.timezone(TIME_ZONE)
        creation_time = timezone.localize(datetime.strptime(struct.creation_time,
                                                            DATETIME_FORMAT))
    else:
        creation_time = None

    instance.observation_variable = observation_variable
    instance.observation_unit = observation_unit
    instance.value = struct.value
    instance.observer = struct.observer
    instance.creation_time = creation_time

    instance.save()
    return instance
