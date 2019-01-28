from copy import deepcopy
from collections import OrderedDict

from rest_framework.exceptions import ValidationError

from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_VARIABLE, OBSERVATION_UNIT,
                                    OBSERVATION_CREATION_TIME, OBSERVER, VALUE,
                                    INSTITUTE_CODE, GERMPLASM_NUMBER,
                                    OBSERVATION_STUDY, ACCESSION,
                                    OBSERVATION_ID)
from vavilov3.conf.settings import DATETIME_FORMAT


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
    {'csv_field_name': 'ACCESSION', 'getter': lambda x: x.accession,
     'setter': lambda obj, val: setattr(obj, 'study', val)},
]
OBSERVATION_VARIABLE_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _OBSERVATION_VARIABLE_CSV_FIELD_CONFS])
