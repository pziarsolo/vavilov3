from vavilov3.entities.metadata import Metadata
from copy import deepcopy
from vavilov3.entities.tags import (
    STUDY_NAME, STUDY_DESCRIPTION, STUDY_ACTIVE, START_DATE, END_DATE,
    LOCATION, CONTACT, PROJECT_NAME)
from vavilov3.views import format_error_message
from rest_framework.exceptions import ValidationError
from datetime import date
from collections import OrderedDict


class StudyValidationError(Exception):
    pass


STUDY_ALLOWED_FIELDS = [STUDY_NAME, STUDY_DESCRIPTION, STUDY_ACTIVE, START_DATE,
                        END_DATE, LOCATION, CONTACT, PROJECT_NAME]


def validate_study_data(data):
    if STUDY_NAME not in data:
        raise StudyValidationError('{} mandatory'.format(STUDY_NAME))
    if STUDY_DESCRIPTION not in data:
        raise StudyValidationError('{} mandatory'.format(STUDY_DESCRIPTION))
    if STUDY_ACTIVE not in data:
        raise StudyValidationError('{} mandatory'.format(STUDY_ACTIVE))

    not_allowed_fields = set(data.keys()).difference(STUDY_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise StudyValidationError(msg)


class StudyStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._metadata = Metadata()

        elif api_data:
            payload = deepcopy(api_data['data'])
            self._data = payload
            if START_DATE in payload:
                self.start_date = payload[START_DATE]
            if END_DATE in payload:
                self.end_date = payload[END_DATE]

            self._metadata = Metadata(api_data['metadata'])

        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        if START_DATE in _data:
            _data[START_DATE] = _data[START_DATE].strftime('%d/%m/%Y')
        if END_DATE in _data:
            _data[END_DATE] = _data[END_DATE].strftime('%d/%m/%Y')
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
        return self._data[STUDY_NAME]

    @name.setter
    def name(self, name):
        self._data[STUDY_NAME] = name

    @property
    def description(self):
        return self._data[STUDY_DESCRIPTION]

    @description.setter
    def description(self, description):
        self._data[STUDY_DESCRIPTION] = description

    @property
    def is_active(self):
        return self._data[STUDY_ACTIVE]

    @is_active.setter
    def is_active(self, is_active: str):
        self._data[STUDY_ACTIVE] = is_active

    @property
    def start_date(self) -> date:
        return self._data[START_DATE]

    @start_date.setter
    def start_date(self, start_date: str):
        if start_date:
            day, month, year = start_date.split('/')
            self._data[START_DATE] = date(int(year), int(month), int(day))

    @property
    def end_date(self) -> date:
        return self._data[END_DATE]

    @end_date.setter
    def end_date(self, end_date: str):
        if end_date:
            day, month, year = end_date.split('/')
            self._data[END_DATE] = date(int(year), int(month), int(day))

    @property
    def contact(self):
        return self._data.get(CONTACT, None)

    @contact.setter
    def contact(self, contact):
        if contact:
            self._data[CONTACT] = contact

    @property
    def location(self):
        return self._data.get(LOCATION, None)

    @location.setter
    def location(self, location):
        if location:
            self._data[LOCATION] = location

    @property
    def project_name(self):
        return self._data.get(PROJECT_NAME, None)

    @project_name.setter
    def project_name(self, project_name):
        if project_name:
            self._data[PROJECT_NAME] = project_name

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.group.name
        self.metadata.is_public = instance.is_public
        accepted_fields = STUDY_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or STUDY_NAME in fields:
            self.name = instance.name
        if fields is None or STUDY_DESCRIPTION in fields:
            self.description = instance.description
        if (instance.is_active is not None and
                (fields is None or STUDY_ACTIVE in fields)):
            self.is_active = instance.is_active
        if fields is None or START_DATE in fields:
            self.start_date = instance.data.get(START_DATE, None)
        if fields is None or END_DATE in fields:
            self.end_date = instance.data.get(END_DATE, None)
        if fields is None or LOCATION in fields:
            self.location = instance.data.get(LOCATION, None)
        if fields is None or CONTACT in fields:
            self.contact = instance.data.get(CONTACT, None)
        if fields is None or PROJECT_NAME in fields:
            self.project_name = instance.data.get(PROJECT_NAME, None)

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = STUDY_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

    def populate_from_csvrow(self, row):

        for field, value in row.items():
            if not value:
                continue
            field_conf = STUDY_CSV_FIELD_CONFS.get(field)

            if field_conf:
                setter = field_conf['setter']
                setter(self, value)


_STUDY_CSV_FIELD_CONFS = [
    {'csv_field_name': 'NAME', 'getter': lambda x: x.name,
     'setter': lambda obj, val: setattr(obj, 'name', val)},
    {'csv_field_name': 'DESCRIPTION', 'getter': lambda x: x.description,
     'setter': lambda obj, val: setattr(obj, 'description', val)},
    {'csv_field_name': 'ACTIVE', 'getter': lambda x: x.is_active,
     'setter': lambda obj, val: setattr(obj, 'is_active', True if val.lower() == 'yes' else False)},
    {'csv_field_name': 'START_DATE', 'getter': lambda x: x.start_date,
     'setter': lambda obj, val: setattr(obj, 'start_date', val)},
    {'csv_field_name': 'END_DATE', 'getter': lambda x: x.end_date,
     'setter': lambda obj, val: setattr(obj, 'end_date', val)},
    {'csv_field_name': 'LOCATION', 'getter': lambda x: x.location,
     'setter': lambda obj, val: setattr(obj, 'location', val)},
    {'csv_field_name': 'CONTACT', 'getter': lambda x: x.contact,
     'setter': lambda obj, val: setattr(obj, 'contact', val)},
    {'csv_field_name': 'PROJECT_NAME', 'getter': lambda x: x.project_name,
     'setter': lambda obj, val: setattr(obj, 'project_name', val)},

]
STUDY_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _STUDY_CSV_FIELD_CONFS])
