from copy import deepcopy
from collections import OrderedDict

from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_VARIABLE_NAME, TRAIT,
                                    OBSERVATION_VARIABLE_DESCRIPTION, METHOD,
                                    DATA_TYPE, UNIT)


class ObservationVariableValidationError(Exception):
    pass


OBSERVATION_VARIABLE_ALLOWED_FIELDS = [OBSERVATION_VARIABLE_NAME,
                                       TRAIT, OBSERVATION_VARIABLE_DESCRIPTION,
                                       METHOD, DATA_TYPE, UNIT]


def validate_observation_variable_data(data):
    if OBSERVATION_VARIABLE_NAME not in data:
        raise ObservationVariableValidationError('{} mandatory'.format(OBSERVATION_VARIABLE_NAME))
    if TRAIT not in data:
        raise ObservationVariableValidationError('{} mandatory'.format(TRAIT))
    if OBSERVATION_VARIABLE_DESCRIPTION not in data:
        raise ObservationVariableValidationError('{} mandatory'.format(OBSERVATION_VARIABLE_DESCRIPTION))
    if METHOD not in data:
        raise ObservationVariableValidationError('{} mandatory'.format(METHOD))
    if DATA_TYPE not in data:
        raise ObservationVariableValidationError('{} mandatory'.format(DATA_TYPE))
    if OBSERVATION_VARIABLE_DESCRIPTION not in data:
        raise ObservationVariableValidationError('{} mandatory'.format(OBSERVATION_VARIABLE_DESCRIPTION))

    not_allowed_fields = set(data.keys()).difference(OBSERVATION_VARIABLE_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise ObservationVariableValidationError(msg)


class ObservationVariableStruct():

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
        return self._data[OBSERVATION_VARIABLE_NAME]

    @name.setter
    def name(self, name):
        self._data[OBSERVATION_VARIABLE_NAME] = name

    @property
    def description(self):
        return self._data[OBSERVATION_VARIABLE_DESCRIPTION]

    @description.setter
    def description(self, description):
        self._data[OBSERVATION_VARIABLE_DESCRIPTION] = description

    @property
    def trait(self):
        return self._data.get(TRAIT, None)

    @trait.setter
    def trait(self, trait):
        self._data[TRAIT] = trait

    @property
    def method(self):
        return self._data[METHOD]

    @method.setter
    def method(self, method: str):
        if method:
            self._data[METHOD] = method

    @property
    def data_type(self) -> str:
        return self._data[DATA_TYPE]

    @data_type.setter
    def data_type(self, data_type: str):
        if data_type:
            self._data[DATA_TYPE] = data_type

    @property
    def unit(self):
        return self._data.get(UNIT, None)

    @unit.setter
    def unit(self, unit):
        if unit:
            self._data[UNIT] = unit

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.group.name
        accepted_fields = OBSERVATION_VARIABLE_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or OBSERVATION_VARIABLE_NAME in fields:
            self.name = instance.name
        if fields is None or OBSERVATION_VARIABLE_DESCRIPTION in fields:
            self.description = instance.description
        if fields is None or TRAIT in fields:
            self.trait = instance.trait
        if fields is None or METHOD in fields:
            self.method = instance.method
        if fields is None or DATA_TYPE in fields:
            self.data_type = instance.data_type.name
        if fields is None or UNIT in fields:
            self.unit = instance.unit

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
    {'csv_field_name': 'NAME', 'getter': lambda x: x.name,
     'setter': lambda obj, val: setattr(obj, 'name', val)},
    {'csv_field_name': 'DESCRIPTION', 'getter': lambda x: x.description,
     'setter': lambda obj, val: setattr(obj, 'description', val)},
    {'csv_field_name': 'TRAIT', 'getter': lambda x: x.trait,
     'setter': lambda obj, val: setattr(obj, 'trait', val)},
    {'csv_field_name': 'METHOD', 'getter': lambda x: x.method,
     'setter': lambda obj, val: setattr(obj, 'method', val)},
    {'csv_field_name': 'DATA_TYPE', 'getter': lambda x: x.data_type,
     'setter': lambda obj, val: setattr(obj, 'data_type', val)},
    {'csv_field_name': 'UNIT', 'getter': lambda x: x.unit,
     'setter': lambda obj, val: setattr(obj, 'unit', val)},
]
OBSERVATION_VARIABLE_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _OBSERVATION_VARIABLE_CSV_FIELD_CONFS])