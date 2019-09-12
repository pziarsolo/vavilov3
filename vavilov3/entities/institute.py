from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError

from vavilov3.models import Institute
from vavilov3.entities.tags import (INSTITUTE_CODE, INSTITUTE_NAME,
                                    INSTITUTE_TYPE, INSTITUTE_ADDRESS,
                                    INSTITUTE_ZIPCODE, INSTITUTE_EMAIL,
                                    INSTITUTE_CITY, INSTITUTE_URL,
                                    INSTITUTE_MANAGER, INSTITUTE_PHONE)
from vavilov3.views import format_error_message
from rest_framework.exceptions import ValidationError
from vavilov3.id_validator import validate_id


class InstituteValidationError(Exception):
    pass


INSTITUTE_ALLOWED_FIELDS = (INSTITUTE_CODE, INSTITUTE_NAME, INSTITUTE_TYPE,
                            INSTITUTE_ADDRESS, INSTITUTE_ZIPCODE, INSTITUTE_EMAIL,
                            INSTITUTE_CITY, INSTITUTE_URL, INSTITUTE_MANAGER,
                            INSTITUTE_PHONE,
                            'num_accessions', 'num_accessionsets',
                            'stats_by_country', 'stats_by_taxa', 'pdcis')


def validate_institute_data(payload):
    if INSTITUTE_CODE not in payload:
        raise InstituteValidationError('{} mandatory'.format(INSTITUTE_CODE))

    not_allowed_fields = set(payload.keys()).difference(INSTITUTE_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowed fields: {}'.format(', '.join(not_allowed_fields))
        raise InstituteValidationError(msg)
    try:
        validate_id(payload[INSTITUTE_CODE])
    except ValueError as msg:
        raise InstituteValidationError(msg)


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

    @property
    def address(self):
        return self._data.get(INSTITUTE_ADDRESS, None)

    @address.setter
    def address(self, address):
        self._data[INSTITUTE_ADDRESS] = address

    @property
    def zipcode(self):
        return self._data.get(INSTITUTE_ZIPCODE, None)

    @zipcode.setter
    def zipcode(self, zipcode):
        self._data[INSTITUTE_ZIPCODE] = zipcode

    @property
    def email(self):
        return self._data.get(INSTITUTE_EMAIL, None)

    @email.setter
    def email(self, email):
        self._data[INSTITUTE_EMAIL] = email

    @property
    def phone(self):
        return self._data.get(INSTITUTE_PHONE, None)

    @phone.setter
    def phone(self, phone):
        self._data[INSTITUTE_PHONE] = phone

    @property
    def city(self):
        return self._data.get(INSTITUTE_CITY, None)

    @city.setter
    def city(self, city):
        self._data[INSTITUTE_CITY] = city

    @property
    def url(self):
        return self._data.get(INSTITUTE_URL, None)

    @url.setter
    def url(self, url):
        self._data[INSTITUTE_URL] = url

    @property
    def manager(self):
        return self._data.get(INSTITUTE_MANAGER, None)

    @manager.setter
    def manager(self, manager):
        self._data[INSTITUTE_MANAGER] = manager

    def _populate_with_instance(self, instance, fields):
        if fields is not None and not set(fields).issubset(INSTITUTE_ALLOWED_FIELDS):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)
        if fields is None or INSTITUTE_CODE in fields:
            self.institute_code = instance.code
        if fields is None or INSTITUTE_NAME in fields:
            self.institute_name = instance.name
        if fields is None or INSTITUTE_TYPE in fields:
            self.institute_type = instance.data.get(INSTITUTE_TYPE, None)
        if fields is None or INSTITUTE_ADDRESS in fields:
            self.address = instance.data.get(INSTITUTE_ADDRESS, None)
        if fields is None or INSTITUTE_ZIPCODE in fields:
            self.zipcode = instance.data.get(INSTITUTE_ZIPCODE, None)
        if fields is None or INSTITUTE_EMAIL in fields:
            self.email = instance.data.get(INSTITUTE_EMAIL, None)
        if fields is None or INSTITUTE_PHONE in fields:
            self.phone = instance.data.get(INSTITUTE_PHONE, None)
        if fields is None or INSTITUTE_CITY in fields:
            self.city = instance.data.get(INSTITUTE_CITY, None)
        if fields is None or INSTITUTE_URL in fields:
            self.url = instance.data.get(INSTITUTE_URL, None)
        if fields is None or INSTITUTE_MANAGER in fields:
            self.manager = instance.data.get(INSTITUTE_MANAGER, None)

        if fields is None or 'num_accessions' in fields:
            self._data['num_accessions'] = instance.num_accessions
        if fields is None or 'num_accessionsets' in fields:
            self._data['num_accessionsets'] = instance.num_accessionsets
        if fields is not None and 'stats_by_country' in fields:
            self._data['stats_by_country'] = instance.stats_by_country(self.user)
        if fields is not None and 'stats_by_taxa' in fields:
            self._data['stats_by_taxa'] = instance.stats_by_taxa(self.user)
        if fields is not None and 'pdcis' in fields:
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
        for field in fields:
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
    {'csv_field_name': 'STREET_POB', 'getter': lambda x: x.address,
     'setter': lambda obj, val: setattr(obj, 'address', val)},
    {'csv_field_name': 'CITY_STATE', 'getter': lambda x: x.city,
     'setter': lambda obj, val: setattr(obj, 'city', val)},
    {'csv_field_name': 'ZIP_CODE', 'getter': lambda x: x.zipcode,
     'setter': lambda obj, val: setattr(obj, 'zipcode', val)},
    {'csv_field_name': 'PHONE', 'getter': lambda x: x.phone,
     'setter': lambda obj, val: setattr(obj, 'phone', val)},
    {'csv_field_name': 'EMAIL', 'getter': lambda x: x.email,
     'setter': lambda obj, val: setattr(obj, 'email', val)},
    {'csv_field_name': 'URL', 'getter': lambda x: x.url,
     'setter': lambda obj, val: setattr(obj, 'url', val)},
    {'csv_field_name': 'MANAGER', 'getter': lambda x: x.manager,
     'setter': lambda obj, val: setattr(obj, 'manager', val)},

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
        except IntegrityError as error:
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
