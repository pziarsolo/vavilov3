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

import re
from datetime import date
from collections import OrderedDict
from copy import deepcopy

import iso3166
from django.db import transaction

from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.views import format_error_message
from vavilov3.models import Group, Country, SeedPetition, Accession
from vavilov3.permissions import is_user_admin
from vavilov3.entities.tags import (PETITIONER_NAME, PETITIONER_TYPE,
                                    PETITIONER_INSTITUTION, PETITIONER_ADDRESS,
                                    PETITIONER_EMAIL, PETITION_DATE,
                                    PETITION_ACCESSIONS, PETITION_COMMENTS,
                                    PETITION_AIM, PETITIONER_CITY,
                                    PETITIONER_POSTAL_CODE, PETITIONER_REGION,
                                    PETITIONER_COUNTRY, INSTITUTE_CODE,
                                    GERMPLASM_NUMBER, PETITION_ID)
from vavilov3.mail import prepare_and_send_seed_petition_mails


class SeedPetitionValidationError(Exception):
    pass


SEED_REQUEST_MANDATORY_FIELDS = [PETITIONER_NAME, PETITIONER_TYPE, PETITIONER_INSTITUTION,
                                 PETITIONER_ADDRESS, PETITIONER_CITY,
                                 PETITIONER_POSTAL_CODE, PETITIONER_REGION,
                                 PETITIONER_COUNTRY, PETITIONER_EMAIL, PETITION_DATE,
                                 PETITION_AIM, PETITION_ACCESSIONS]
SEED_REQUEST_ALLOWED_FIELDS = SEED_REQUEST_MANDATORY_FIELDS + [PETITION_COMMENTS, PETITION_ID]


def validate_seed_petition_data(data):
    for mandatory_field in SEED_REQUEST_MANDATORY_FIELDS:
        if mandatory_field not in data:
            raise SeedPetitionValidationError('{} mandatory'.format(mandatory_field))

    not_allowed_fields = set(data.keys()).difference(SEED_REQUEST_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowed fields: {}'.format(', '.join(not_allowed_fields))
        raise SeedPetitionValidationError(msg)

    country = data[PETITIONER_COUNTRY]
    if country not in iso3166.countries_by_alpha3.keys():
        msg = 'Country must have 3 letter and must exist {}'
        raise SeedPetitionValidationError(msg.format(country))
    email = data[PETITIONER_EMAIL]
    if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
        raise SeedPetitionValidationError('email is malformed {}'.format(email))


class SeedPetitionStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._metadata = Metadata()

        elif api_data:
            payload = deepcopy(api_data['data'])
            if PETITION_DATE in payload:
                date_str = payload.pop(PETITION_DATE)
            self._data = payload
            self.petition_date = date_str
            self._metadata = Metadata(api_data['metadata'])

        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        if PETITION_DATE in _data:
            _data[PETITION_DATE] = _data[PETITION_DATE].strftime('%Y/%m/%d')
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
    def petition_id(self):
        return self._data.get(PETITION_ID, None)

    @petition_id.setter
    def petition_id(self, name):
        self._data[PETITION_ID] = name

    @property
    def petitioner_name(self):
        return self._data.get(PETITIONER_NAME, None)

    @petitioner_name.setter
    def petitioner_name(self, name):
        self._data[PETITIONER_NAME] = name

    @property
    def petitioner_type(self):
        return self._data.get(PETITIONER_TYPE, None)

    @petitioner_type.setter
    def petitioner_type(self, type_):
        self._data[PETITIONER_TYPE] = type_

    @property
    def petitioner_institution(self):
        return self._data.get(PETITIONER_INSTITUTION, None)

    @petitioner_institution.setter
    def petitioner_institution(self, institution):
        self._data[PETITIONER_INSTITUTION] = institution

    @property
    def petitioner_address(self):
        return self._data.get(PETITIONER_ADDRESS, None)

    @petitioner_address.setter
    def petitioner_address(self, address):
        self._data[PETITIONER_ADDRESS] = address

    @property
    def petitioner_city(self):
        return self._data.get(PETITIONER_CITY, None)

    @petitioner_city.setter
    def petitioner_city(self, city):
        self._data[PETITIONER_CITY] = city

    @property
    def petitioner_postal_code(self):
        return self._data.get(PETITIONER_POSTAL_CODE, None)

    @petitioner_postal_code.setter
    def petitioner_postal_code(self, postal_code):
        self._data[PETITIONER_POSTAL_CODE] = postal_code

    @property
    def petitioner_region(self):
        return self._data.get(PETITIONER_REGION, None)

    @petitioner_region.setter
    def petitioner_region(self, region):
        self._data[PETITIONER_REGION] = region

    @property
    def petitioner_country(self):
        return self._data.get(PETITIONER_COUNTRY, None)

    @petitioner_country.setter
    def petitioner_country(self, country):
        if country not in iso3166.countries_by_alpha3.keys():
            msg = 'Country must have 3 letter and must exist {}'
            raise SeedPetitionValidationError(msg.format(country))
        self._data[PETITIONER_COUNTRY] = country

    @property
    def petitioner_email(self):
        return self._data.get(PETITIONER_EMAIL, None)

    @petitioner_email.setter
    def petitioner_email(self, email):
        if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
            raise SeedPetitionValidationError('email is malformed {}'.format(email))
        self._data[PETITIONER_EMAIL] = email

    @property
    def petition_date(self) -> date:
        return self._data.get(PETITION_DATE, None)

    @petition_date.setter
    def petition_date(self, petition_date: str):
        if petition_date:
            year, month, day = petition_date.split('/')
            self._data[PETITION_DATE] = date(int(year), int(month), int(day))

    @property
    def petition_aim(self):
        return self._data.get(PETITION_AIM, None)

    @petition_aim.setter
    def petition_aim(self, aim):
        self._data[PETITION_AIM] = aim

    @property
    def petition_comments(self):
        return self._data.get(PETITION_COMMENTS, None)

    @petition_comments.setter
    def petition_comments(self, comments):
        self._data[PETITION_COMMENTS] = comments

    @property
    def petition_accessions(self):
        return self._data.get(PETITION_ACCESSIONS, None)

    @petition_accessions.setter
    def petition_accessions(self, accessions):
        self._data[PETITION_ACCESSIONS] = accessions

    def _populate_with_instance(self, instance, fields):
        accepted_fields = SEED_REQUEST_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or PETITION_ID in fields:
            self.petition_id = instance.petition_id
        if fields is None or PETITIONER_NAME in fields:
            self.petitioner_name = instance.petitioner_name
        if fields is None or PETITIONER_TYPE in fields:
            self.petitioner_type = instance.petitioner_type
        if fields is None or PETITIONER_INSTITUTION in fields:
            self.petitioner_institution = instance.petitioner_institution

        if fields is None or PETITIONER_ADDRESS in fields:
            self.petitioner_address = instance.petitioner_address
        if fields is None or PETITIONER_CITY in fields:
            self.petitioner_city = instance.petitioner_city
        if fields is None or PETITIONER_POSTAL_CODE in fields:
            self.petitioner_postal_code = instance.petitioner_postal_code
        if fields is None or PETITIONER_REGION in fields:
            self.petitioner_region = instance.petitioner_region
        if fields is None or PETITIONER_COUNTRY in fields:
            self.petitioner_country = instance.petitioner_country.code
        if fields is None or PETITIONER_EMAIL in fields:
            self.petitioner_email = instance.petitioner_email
        if fields is None or PETITION_DATE in fields:
            self.petition_date = instance.petition_date.strftime('%Y/%m/%d')
        if fields is None or PETITION_AIM in fields:
            self.petition_aim = instance.petition_aim
        if fields is None or PETITION_COMMENTS in fields:
            self.petition_comments = instance.petition_comments

        if fields is None or PETITION_ACCESSIONS in fields:
            accessions = []
            for accession_instance in instance.requested_accessions.all():
                accessions.append(
                    {INSTITUTE_CODE: accession_instance.institute.code,
                     GERMPLASM_NUMBER: accession_instance.germplasm_number})
            self.petition_accessions = accessions

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = SEED_PETITION_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

#     def populate_from_csvrow(self, row):
#
#         for field, value in row.items():
#             if not value:
#                 continue
#             field_conf = STUDY_CSV_FIELD_CONFS.get(field)
#
#             if field_conf:
#                 setter = field_conf['setter']
#                 setter(self, value)


def build_accesion_list(seed_petition):
    acce_str = []
    for acc in seed_petition.petition_accessions:
        acce_str.append('{}:{}'.format(acc[INSTITUTE_CODE], acc[GERMPLASM_NUMBER]))
    return ';'.join(acce_str)


_SEED_PETITION_CSV_FIELD_CONFS = [
    {'csv_field_name': 'PETITION ID', 'getter': lambda x: x.petition_id},
    {'csv_field_name': 'NAME', 'getter': lambda x: x.petitioner_name},
    {'csv_field_name': 'TYPE', 'getter': lambda x: x.petitioner_type},
    {'csv_field_name': 'INSTITUTION', 'getter': lambda x: x.petitioner_institution},
    {'csv_field_name': 'ADDRESS', 'getter': lambda x: x.petitioner_address},
    {'csv_field_name': 'CITY', 'getter': lambda x: x.petitioner_city},
    {'csv_field_name': 'POSTAL_CODE', 'getter': lambda x: x.petitioner_postal_code},
    {'csv_field_name': 'COUNTY', 'getter': lambda x: x.petitioner_country},
    {'csv_field_name': 'EMAIL', 'getter': lambda x: x.petitioner_email},
    {'csv_field_name': 'PETITION_DATE', 'getter': lambda x: x.petition_date.strftime('%Y/%m/%d')},
    {'csv_field_name': 'AIM', 'getter': lambda x: x.petition_aim},
    {'csv_field_name': 'COMMENTS', 'getter': lambda x: x.petition_comments},
    {'csv_field_name': 'ACCESSIONS', 'getter': build_accesion_list},
]
SEED_PETITION_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _SEED_PETITION_CSV_FIELD_CONFS])


def create_seed_petition_in_db(api_data, user=None, is_public=None):
    # when we are creating
    try:
        struct = SeedPetitionStruct(api_data=api_data)
    except SeedPetitionValidationError as error:
        raise ValueError(error)

    try:
        country = Country.objects.get(code=struct.petitioner_country)
    except Country.DoesNotExist:
        raise ValueError('given country does not exist {}'.format(struct.petitioner_country))

    with transaction.atomic():
        seed_petition = SeedPetition.objects.create(
            petitioner_name=struct.petitioner_name,
            petitioner_type=struct.petitioner_type,
            petitioner_institution=struct.petitioner_institution,
            petitioner_address=struct.petitioner_address,
            petitioner_city=struct.petitioner_city,
            petitioner_postal_code=struct.petitioner_postal_code,
            petitioner_region=struct.petitioner_region,
            petitioner_country=country,
            petitioner_email=struct.petitioner_email,
            petition_date=date.today(),
            petition_aim=struct.petition_aim,
            petition_comments=struct.petition_comments)

        for accession in struct.petition_accessions:
            try:
                accession_db = Accession.objects.get(institute__code=accession[INSTITUTE_CODE],
                                                     germplasm_number=accession[GERMPLASM_NUMBER])
            except Accession.DoesNotExist:
                msg = 'This accession does not exists: {}:{}'
                msg = msg.format(accession[INSTITUTE_CODE], accession[GERMPLASM_NUMBER])
                raise ValueError(msg)
            seed_petition.requested_accessions.add(accession_db)
    try:
        prepare_and_send_seed_petition_mails(struct)
    except RuntimeError as error:
        raise ValueError(error)

    return seed_petition


def update_seed_petition_in_db(validated_data, instance, user):
    study_struct = SeedPetitionStruct(api_data=validated_data)
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
    instance.save()
    return instance
