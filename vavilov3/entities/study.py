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

from datetime import date
from collections import OrderedDict
from copy import deepcopy

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.entities.tags import (
    STUDY_NAME, STUDY_DESCRIPTION, STUDY_ACTIVE, START_DATE, END_DATE,
    LOCATION, CONTACT, PROJECT_NAME, SEASON, INSTITUTION)
from vavilov3.views import format_error_message
from vavilov3.models import Group, Study, Project
from vavilov3.permissions import is_user_admin
from vavilov3.id_validator import validate_name


class StudyValidationError(Exception):
    pass


STUDY_ALLOWED_FIELDS = [STUDY_NAME, STUDY_DESCRIPTION, STUDY_ACTIVE, START_DATE,
                        END_DATE, LOCATION, CONTACT, PROJECT_NAME, SEASON,
                        INSTITUTION]


def validate_study_data(data):
    if STUDY_NAME not in data:
        raise StudyValidationError('{} mandatory'.format(STUDY_NAME))
    if STUDY_DESCRIPTION not in data:
        raise StudyValidationError('{} mandatory'.format(STUDY_DESCRIPTION))

    not_allowed_fields = set(data.keys()).difference(STUDY_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise StudyValidationError(msg)
    try:
        validate_name(data[STUDY_NAME])
    except ValueError as msg:
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
            _data[START_DATE] = _data[START_DATE].strftime('%Y/%m/%d')
        if END_DATE in _data:
            _data[END_DATE] = _data[END_DATE].strftime('%Y/%m/%d')
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
        return self._data.get(STUDY_ACTIVE, None)

    @is_active.setter
    def is_active(self, is_active):
        self._data[STUDY_ACTIVE] = is_active

    @property
    def start_date(self) -> date:
        return self._data.get(START_DATE, None)

    @start_date.setter
    def start_date(self, start_date: str):
        if start_date:
            year, month, day = start_date.split('/')
            self._data[START_DATE] = date(int(year), int(month), int(day))

    @property
    def end_date(self) -> date:
        return self._data.get(END_DATE, None)

    @end_date.setter
    def end_date(self, end_date: str):
        if end_date:
            year, month, day = end_date.split('/')
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

    @property
    def season(self):
        return self._data.get(SEASON, None)

    @season.setter
    def season(self, season):
        if season:
            self._data[SEASON] = season

    @property
    def institution(self):
        return self._data.get(INSTITUTION, None)

    @institution.setter
    def institution(self, institution):
        if institution:
            self._data[INSTITUTION] = institution

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
        if instance.is_active is not None and fields is not None and STUDY_ACTIVE in fields:
            self.is_active = instance.is_active
        if fields is None or START_DATE in fields:
            if instance.start_date is not None:
                self.start_date = instance.start_date.strftime('%Y/%m/%d')
            else:
                self.start_date = None
        if fields is None or END_DATE in fields:
            if instance.end_date is not None:
                self.end_date = instance.end_date.strftime('%Y/%m/%d')
            else:
                self.end_date = None
        if fields is None or LOCATION in fields:
            self.location = instance.data.get(LOCATION, None)
        if fields is None or CONTACT in fields:
            self.contact = instance.data.get(CONTACT, None)
        if fields is None or PROJECT_NAME in fields:
            self.project_name = instance.data.get(PROJECT_NAME, None)
        if fields is None or SEASON in fields:
            self.season = instance.data.get(SEASON, None)
        if fields is None or INSTITUTION in fields:
            self.institution = instance.data.get(INSTITUTION, None)

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


_SEED_REQUEST_CSV_FIELD_CONFS = [
    {'csv_field_name': 'NAME', 'getter': lambda x: x.name,
     'setter': lambda obj, val: setattr(obj, 'name', val)},
    {'csv_field_name': 'DESCRIPTION', 'getter': lambda x: x.description,
     'setter': lambda obj, val: setattr(obj, 'description', val)},
    # {'csv_field_name': 'ACTIVE', 'getter': lambda x: x.is_active,
    # 'setter': lambda obj, val: setattr(obj, 'is_active', True if val.lower() == 'yes' else False)},
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
    {'csv_field_name': 'SEASON', 'getter': lambda x: x.season,
     'setter': lambda obj, val: setattr(obj, 'season', val)},
    {'csv_field_name': 'INSTITUTION', 'getter': lambda x: x.institution,
     'setter': lambda obj, val: setattr(obj, 'institution', val)},

]
STUDY_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _SEED_REQUEST_CSV_FIELD_CONFS])


def create_study_in_db(api_data, user, is_public=None):
    # when we are creating
    try:
        study_struct = StudyStruct(api_data=api_data)
    except StudyValidationError as error:
        print(error)
        raise

    if (study_struct.metadata.group or study_struct.metadata.is_public):
        msg = 'can not set group or is public while creating the study'
        raise ValueError(msg)

    if study_struct.project_name:
        try:
            project = Project.objects.get(name=study_struct.project_name)
        except Project.DoesNotExist:
            msg = '{} does not exist in database'
            msg = msg.format(study_struct.project_name)
            raise ValueError(msg)
    else:
        project = None

    # in the doc we must enter whole document
    if is_public is None:
        is_public = False

    group = user.groups.first()
    study_struct.metadata.is_public = is_public
    study_struct.metadata.group = group.name

    with transaction.atomic():
        try:
            study = Study.objects.create(
                name=study_struct.name,
                description=study_struct.description,
                is_active=study_struct.is_active,
                project=project,
                group=group,
                is_public=is_public,
                start_date=study_struct.start_date,
                end_date=study_struct.end_date,
                data=study_struct.data)
        except IntegrityError:
            msg = 'This study already exists in db: {}'.format(study_struct.name)
            raise ValueError(msg)

    return study


def update_study_in_db(validated_data, instance, user):
    study_struct = StudyStruct(api_data=validated_data)
    if (study_struct.name != instance.name):
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))

    group_belong_to_user = bool(user.groups.filter(name=study_struct.metadata.group).count())

    if not group_belong_to_user and not is_user_admin(user):
        msg = 'Can not change ownership if group does not belong to you : {}'
        msg = msg.format(study_struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    try:
        group = Group.objects.get(name=study_struct.metadata.group)
    except Group.DoesNotExist:
        msg = 'Provided group does not exist in db: {}'
        msg = msg.format(study_struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    instance.description = study_struct.description
    instance.is_active = study_struct.is_active
    instance.group = group
    instance.is_public = study_struct.metadata.is_public
    instance.data = study_struct.data
    instance.start_date = study_struct.start_date
    instance.end_date = study_struct.end_date
    instance.save()
    return instance
