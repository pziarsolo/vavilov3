from copy import deepcopy
from collections import OrderedDict

from rest_framework.exceptions import ValidationError

from vavilov3_accession.entities.tags import (INSTITUTE_CODE, GERMPLASM_NUMBER,
                                              IS_SAVE_DUPLICATE, IS_AVAILABLE,
                                              CONSTATUS, PASSPORTS, PUID,
                                              VALID_CONSERVATION_STATUSES)
from vavilov3_accession.entities.metadata import Metadata
from vavilov3_accession.entities.passport import (PassportStruct,
                                                  validate_passport_data,
                                                  PASSPORT_CSV_FIELD_CONFS,
                                                  merge_passports)
from vavilov3_accession.views import format_error_message


class AccessionValidationError(Exception):
    pass


def validate_accession_data(data):
    if INSTITUTE_CODE not in data:
        raise AccessionValidationError('{} mandatory'.format(INSTITUTE_CODE))
    if GERMPLASM_NUMBER not in data:
        raise AccessionValidationError('{} mandatory'.format(GERMPLASM_NUMBER))
    if (CONSTATUS in data and
            data[CONSTATUS] not in VALID_CONSERVATION_STATUSES):
        msg = 'Conservation status ({})must be one of this: {}'
        raise AccessionValidationError(msg.format(
            data[CONSTATUS], ','.join(VALID_CONSERVATION_STATUSES)))

    if PASSPORTS in data:
        for passport in data[PASSPORTS]:
            validate_passport_data(passport)


class AccessionStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._passports = []
            self._metadata = Metadata()

        elif api_data:
            payload = deepcopy(api_data['data'])
            passports = payload.get(PASSPORTS, [])
            self._data = payload
            self._passports = [PassportStruct(p) for p in passports]
            self._metadata = Metadata(api_data['metadata'])
        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._passports = None
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        if self._passports:
            _data[PASSPORTS] = [passport.data for passport in self._passports]
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
    def passports(self):
        return self._passports

    @passports.setter
    def passports(self, passports):
        self._passports = passports

    @property
    def puid(self):
        return self._data.get(PUID, None)

    @puid.setter
    def puid(self, puid):
        self._data[PUID] = puid

    @property
    def institute_code(self):
        return self._data.get(INSTITUTE_CODE, None)

    @institute_code.setter
    def institute_code(self, code):
        self._data[INSTITUTE_CODE] = code

    @property
    def germplasm_number(self):
        return self._data.get(GERMPLASM_NUMBER, None)

    @germplasm_number.setter
    def germplasm_number(self, number):
        self._data[GERMPLASM_NUMBER] = number

    @property
    def is_save_duplicate(self):
        return self._data.get(IS_SAVE_DUPLICATE, None)

    @is_save_duplicate.setter
    def is_save_duplicate(self, is_save_duplicate):
        self._data[IS_SAVE_DUPLICATE] = is_save_duplicate

    @property
    def is_available(self):
        return self._data.get(IS_AVAILABLE, None)

    @is_available.setter
    def is_available(self, is_available):
        self._data[IS_AVAILABLE] = is_available

    @property
    def conservation_status(self):
        return self._data.get(CONSTATUS, None)

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

    @conservation_status.setter
    def conservation_status(self, conservation_status):
        if conservation_status not in VALID_CONSERVATION_STATUSES:
            msg = '{} must be one of {}'.format(
                conservation_status,
                ', '.join(VALID_CONSERVATION_STATUSES))
            raise AccessionValidationError(msg)
        self._data[CONSTATUS] = conservation_status

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.group.name
        self.metadata.is_public = instance.is_public
        accepted_fields = [INSTITUTE_CODE, GERMPLASM_NUMBER, IS_AVAILABLE,
                           CONSTATUS, PASSPORTS, 'genera', 'countries']
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or INSTITUTE_CODE in fields:
            self.institute_code = instance.institute.code
        if fields is None or GERMPLASM_NUMBER in fields:
            self.germplasm_number = instance.germplasm_number
        if (instance.is_available is not None and
                (fields is None or IS_AVAILABLE in fields)):
            self.is_available = instance.is_available
        if (instance.conservation_status is not None and
                (fields is None or CONSTATUS in fields)):
            self.conservation_status = instance.conservation_status

        if instance.genera and fields and 'genera' in fields:
            self.genera = instance.genera

        if instance.countries and fields and 'countries' in fields:
            self.countries = instance.countries

        if fields is None or PASSPORTS in fields:
            passports = []
            for passport_instance in instance.passports.all():
                passport_struct = PassportStruct(instance=passport_instance,
                                                 fields=fields)
                passports.append(passport_struct)
            self.passports = passports

    def to_list_representation(self, fields):
        items = []
        for field in fields[:5]:
            getter = ACCESSION_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))

        passports = self.passports
        if passports:
            if len(passports) == 1:
                passport = passports[0]
            else:
                passport = merge_passports(passports)
            passport_items = passport.to_list_representation(fields[5:])
        else:
            passport_items = [''] * len(fields[5:])
        items.extend(passport_items)
        return items

    def populate_from_csvrow(self, row):
        _passport = PassportStruct()

        for field, value in row.items():
            if not value:
                continue
            field_conf = ACCESSION_CSV_FIELD_CONFS.get(field)
            if not field_conf:
                continue

            setter = field_conf['setter']
            setter(self, value)

            passport_field_conf = PASSPORT_CSV_FIELD_CONFS.get(field)
            if not passport_field_conf:
                continue

            setter = passport_field_conf['setter']
            setter(_passport, value)
        self.passports = [_passport]


_ACCESSION_CSV_FIELD_CONFS = [
    {'csv_field_name': 'PUID', 'getter': lambda x: x.puid,
     'setter': lambda obj, val: setattr(obj, 'puid', val)},
    {'csv_field_name': 'INSTCODE', 'getter': lambda x: x.institute_code,
     'setter': lambda obj, val: setattr(obj, 'institute_code', val)},
    {'csv_field_name': 'ACCENUMB', 'getter': lambda x: x.germplasm_number,
     'setter': lambda obj, val: setattr(obj, 'germplasm_number', val)},
    {'csv_field_name': 'CONSTATUS', 'getter': lambda x: x.conservation_status,
     'setter': lambda obj, val: setattr(obj, 'conservation_status', val)},
    {'csv_field_name': 'IS_AVAILABLE', 'getter': lambda x: x.is_available,
     'setter': lambda obj, val: setattr(obj, 'is_available', val)},
]
ACCESSION_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _ACCESSION_CSV_FIELD_CONFS])
