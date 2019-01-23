from copy import deepcopy
from collections import OrderedDict

from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_UNIT_NAME,
                                    OBSERVATION_UNIT_LEVEL,
                                    OBSERVATION_UNIT_REPLICATE,
                                    INSTITUTE_CODE, GERMPLASM_NUMBER, ACCESSION,
                                    OBSERVATION_UNIT_STUDY, PLANTS)


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
