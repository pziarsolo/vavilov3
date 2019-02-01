from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError

from vavilov3.models import Institute
from vavilov3.entities.tags import (INSTITUTE_CODE, INSTITUTE_NAME,
                                    INSTITUTE_TYPE)


class InstituteValidationError(Exception):
    pass


def validate_institute_data(payload):
    if INSTITUTE_CODE not in payload:
        raise InstituteValidationError('{} mandatory'.format(INSTITUTE_CODE))


class InstituteStruct():

    def __init__(self, api_data=None, instance=None, fields=None, user=None):
        self.user = user
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
        elif api_data:
            validate_institute_data(api_data)
            self._data = api_data
        elif instance:
            self._data = {}
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        return self._data

    def get_api_document(self):
        return self.data

    @property
    def institute_code(self):
        return self._data.get(INSTITUTE_CODE, None)

    @institute_code.setter
    def institute_code(self, code):
        self._data[INSTITUTE_CODE] = code

    @property
    def institute_name(self):
        return self._data.get(INSTITUTE_NAME, None)

    @institute_name.setter
    def institute_name(self, name):
        self._data[INSTITUTE_NAME] = name

    @property
    def institute_type(self):
        return self._data.get(INSTITUTE_TYPE, None)

    @institute_type.setter
    def institute_type(self, type_):
        self._data[INSTITUTE_TYPE] = type_

    def _populate_with_instance(self, instance, fields):
        if fields is None or 'instituteCode' in fields:
            self.institute_code = instance.code
        if fields is None or 'name' in fields:
            self.institute_name = instance.name
        if fields is None or 'num_accessions' in fields:
            self._data['num_accessions'] = instance.num_accessions
        if fields is None or 'num_accessionsets' in fields:
            self._data['num_accessionsets'] = instance.num_accessionsets
        if fields is None or 'stats_by_country' in fields:
            self._data['stats_by_country'] = instance.stats_by_country(self.user)
        if fields is None or 'stats_by_taxa' in fields:
            self._data['stats_by_taxa'] = instance.stats_by_taxa(self.user)
        if fields is None or 'pdcis' in fields:
            self._data['pdcis'] = instance.pdcis

    def populate_from_csvrow(self, row):
        for field, value in row.items():
            if not value:
                continue
            field_conf = INSTITUTE_CSV_FIELD_CONFS.get(field)
            if not field_conf:
                continue

            setter = field_conf['setter']
            setter(self, value)

    def to_list_representation(self, fields):
        items = []
        for field in fields[:5]:
            getter = INSTITUTE_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items


_INSTITUTE_CSV_FIELD_CONFS = [
    {'csv_field_name': 'INSTCODE', 'getter': lambda x: x.institute_code,
     'setter': lambda obj, val: setattr(obj, 'institute_code', val)},
    {'csv_field_name': 'FULL_NAME', 'getter': lambda x: x.institute_name,
     'setter': lambda obj, val: setattr(obj, 'institute_name', val)},
    {'csv_field_name': 'TYPE', 'getter': lambda x: x.institute_type,
     'setter': lambda obj, val: setattr(obj, 'institute_type', val)},

]
INSTITUTE_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f)
                                         for f in _INSTITUTE_CSV_FIELD_CONFS])


def create_institute_in_db(api_data):
    try:
        institute_struct = InstituteStruct(api_data)
    except InstituteValidationError as error:
        print(error)
        raise

    with transaction.atomic():
        try:
            institute = Institute.objects.create(
                code=institute_struct.institute_code,
                name=institute_struct.institute_name,
                data=institute_struct.data)
        except IntegrityError:
            msg = '{} already exist in db'
            msg = msg .format(institute_struct.institute_code)
            raise ValueError(msg)
        return institute


def update_institute_in_db(api_data, instance):
    try:
        institute_struct = InstituteStruct(api_data)
    except InstituteValidationError as error:
        raise ValueError(error)

    if institute_struct.institute_code != instance.code:
        raise ValueError('Can not change id in an update operation')

    instance.name = institute_struct.institute_name
    instance.data = institute_struct.data
    instance.save()

    return instance
