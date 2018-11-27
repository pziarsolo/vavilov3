import sys
from copy import deepcopy
from collections import OrderedDict

from rest_framework.exceptions import ValidationError

from vavilov3_accession.entities.tags import (INSTITUTE_CODE, GERMPLASM_NUMBER,
                                              ACCESSIONS, ACCESSIONSET_NUMBER)
from vavilov3_accession.entities.metadata import Metadata
from vavilov3_accession.views import format_error_message


class AccessionSetValidationError(Exception):
    pass


def validate_accessionset_data(data):
    if INSTITUTE_CODE not in data:
        raise AccessionSetValidationError('{} mandatory'.format(INSTITUTE_CODE))
    if ACCESSIONSET_NUMBER not in data:
        raise AccessionSetValidationError('{} mandatory'.format(ACCESSIONSET_NUMBER))

    if ACCESSIONS in data:
        for accession in data[ACCESSIONS]:
            if INSTITUTE_CODE not in accession:
                msg = '{} mandatory in accession id'.format(INSTITUTE_CODE)
                raise AccessionSetValidationError(msg)
            if GERMPLASM_NUMBER not in accession:
                msg = '{} mandatory in accession id'.format(GERMPLASM_NUMBER)
                raise AccessionSetValidationError(msg)


class AccessionSetStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._accessions = []
            self._metadata = Metadata()

        elif api_data:
            payload = deepcopy(api_data['data'])
            self._accessions = payload.get(ACCESSIONS, [])
            self._data = payload
            self._metadata = Metadata(api_data['metadata'])
        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._accessions = None
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        if self.accessions:
            _data[ACCESSIONS] = self.accessions
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
    def accessions(self):
        return self._accessions

    @accessions.setter
    def accessions(self, accessions):
        self._accessions = accessions

    @property
    def institute_code(self):
        return self._data.get(INSTITUTE_CODE, None)

    @institute_code.setter
    def institute_code(self, code):
        self._data[INSTITUTE_CODE] = code

    @property
    def accessionset_number(self):
        return self._data.get(ACCESSIONSET_NUMBER, None)

    @accessionset_number.setter
    def accessionset_number(self, number):
        self._data[ACCESSIONSET_NUMBER] = number

    @property
    def genera(self):
        return self._data.get('genera', None)

    @genera.setter
    def genera(self, genera):
        self._data['genera'] = genera

    @property
    def countries(self):
        return self._data.get('countries', None)

    @countries.setter
    def countries(self, countries):
        self._data['countries'] = countries

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.group.name
        self.metadata.is_public = instance.is_public
        accepted_fields = [INSTITUTE_CODE, ACCESSIONSET_NUMBER, ACCESSIONS,
                           'genera', 'countries']
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or INSTITUTE_CODE in fields:
            self.institute_code = instance.institute.code
        if fields is None or ACCESSIONSET_NUMBER in fields:
            self.accessionset_number = instance.accessionset_number

        if instance.genera and fields and 'genera' in fields:
            self.genera = instance.genera

        if instance.countries and fields and 'countries' in fields:
            self.countries = instance.countries

        if fields is None or ACCESSIONS in fields:
            accessions = []
            for accession_instance in instance.accessions.all():
                accessions.append(
                    {INSTITUTE_CODE: accession_instance.institute.code,
                     GERMPLASM_NUMBER: accession_instance.germplasm_number})
            self.accessions = accessions

    def to_list_representation(self, accessionset_fields):
        items = []
        for field in accessionset_fields:
            getter = ACCESSIONSET_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

    def populate_from_csvrow(self, row):
        for field, value in row.items():
            if not value:
                continue
            field_conf = ACCESSIONSET_CSV_FIELD_CONFS.get(field)
            if not field_conf:
                continue

            setter = field_conf['setter']
            setter(self, value)


def get_accessions(accessionset):
    accessions = []
    for accession in accessionset.accessions:
        accessions.append('{}:{}'.format(accession.institute_code, accession.germplasm_number))
    return ';'.join(accessions)


def set_accessions(accessionset, val):
    accessions = []
    try:
        for accession in val.split(';'):
            institute, number = accession.split(':')
            accessions.append({INSTITUTE_CODE: institute, GERMPLASM_NUMBER: number})

    except ValueError:
        msg = 'Accessions field on {} not well formated'.format(accessionset.accessionset_number)
        sys.stderr.write(msg + '\n')
        raise ValueError(msg)
    if accessions:
        accessionset.accessions = accessions


def build_accessions(accessionset):
    accessions = []
    for accession in accessionset.accessions:
        accessions.append("{}:{}".format(accession[INSTITUTE_CODE], accession[GERMPLASM_NUMBER]))
    return ";".join(accessions)


_ACCESSIONSET_CSV_FIELD_CONFS = [
    {'csv_field_name': 'INSTCODE', 'getter': lambda x: x.institute_code,
     'setter': lambda obj, val: setattr(obj, 'institute_code', val)},
    {'csv_field_name': 'ACCESETNUMB', 'getter': lambda x: x.accessionset_number,
     'setter': lambda obj, val: setattr(obj, 'accessionset_number', val)},
    {'csv_field_name': 'ACCESSIONS', 'getter': build_accessions,
     'setter': set_accessions},
]
ACCESSIONSET_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _ACCESSIONSET_CSV_FIELD_CONFS])
