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
import smtplib

import iso3166

from django.db import transaction
from django.core.mail import send_mass_mail

from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.views import format_error_message
from vavilov3.models import Group, Country, SeedRequest, Accession
from vavilov3.permissions import is_user_admin
from vavilov3.entities.tags import (REQUESTER_NAME, REQUESTER_TYPE,
                                    REQUESTER_INSTITUTION, REQUESTER_ADDRESS,
                                    REQUESTER_EMAIL, REQUEST_DATE,
                                    REQUESTED_ACCESSIONS, REQUEST_COMMENTS,
                                    REQUEST_AIM, REQUESTER_CITY,
                                    REQUESTER_POSTAL_CODE, REQUESTER_REGION,
                                    REQUESTER_COUNTRY, INSTITUTE_CODE,
                                    GERMPLASM_NUMBER, REQUEST_UID)
from vavilov3.mail import prepare_mail_request


class SeedRequestValidationError(Exception):
    pass


SEED_REQUEST_MANDATORY_FIELDS = [REQUESTER_NAME, REQUESTER_TYPE, REQUESTER_INSTITUTION,
                                 REQUESTER_ADDRESS, REQUESTER_CITY,
                                 REQUESTER_POSTAL_CODE, REQUESTER_REGION,
                                 REQUESTER_COUNTRY, REQUESTER_EMAIL, REQUEST_DATE,
                                 REQUEST_AIM, REQUESTED_ACCESSIONS]
SEED_REQUEST_ALLOWED_FIELDS = SEED_REQUEST_MANDATORY_FIELDS + [REQUEST_COMMENTS,
                                                               REQUEST_UID]


def validate_seed_request_data(data):
    for mandatory_field in SEED_REQUEST_MANDATORY_FIELDS:
        if mandatory_field not in data:
            raise SeedRequestValidationError('{} mandatory'.format(mandatory_field))

    not_allowed_fields = set(data.keys()).difference(SEED_REQUEST_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowed fields: {}'.format(', '.join(not_allowed_fields))
        raise SeedRequestValidationError(msg)

    country = data[REQUESTER_COUNTRY]
    if country not in iso3166.countries_by_alpha3.keys():
        msg = 'Country must have 3 letter and must exist {}'
        raise SeedRequestValidationError(msg.format(country))
    email = data[REQUESTER_EMAIL]
    if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
        raise SeedRequestValidationError('email is malformed {}'.format(email))


class SeedRequestStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._metadata = Metadata()

        elif api_data:
            payload = deepcopy(api_data['data'])
            if REQUEST_DATE in payload:
                date_str = payload.pop(REQUEST_DATE)
            self._data = payload
            self.request_date = date_str
            self._metadata = Metadata(api_data['metadata'])

        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        if REQUEST_DATE in _data:
            _data[REQUEST_DATE] = _data[REQUEST_DATE].strftime('%Y/%m/%d')
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
    def request_uid(self):
        return self._data.get(REQUEST_UID, None)

    @request_uid.setter
    def request_uid(self, name):
        self._data[REQUEST_UID] = name

    @property
    def requester_name(self):
        return self._data.get(REQUESTER_NAME, None)

    @requester_name.setter
    def requester_name(self, name):
        self._data[REQUESTER_NAME] = name

    @property
    def requester_type(self):
        return self._data.get(REQUESTER_TYPE, None)

    @requester_type.setter
    def requester_type(self, type_):
        self._data[REQUESTER_TYPE] = type_

    @property
    def requester_institution(self):
        return self._data.get(REQUESTER_INSTITUTION, None)

    @requester_institution.setter
    def requester_institution(self, institution):
        self._data[REQUESTER_INSTITUTION] = institution

    @property
    def requester_address(self):
        return self._data.get(REQUESTER_ADDRESS, None)

    @requester_address.setter
    def requester_address(self, address):
        self._data[REQUESTER_ADDRESS] = address

    @property
    def requester_city(self):
        return self._data.get(REQUESTER_CITY, None)

    @requester_city.setter
    def requester_city(self, city):
        self._data[REQUESTER_CITY] = city

    @property
    def requester_postal_code(self):
        return self._data.get(REQUESTER_POSTAL_CODE, None)

    @requester_postal_code.setter
    def requester_postal_code(self, postal_code):
        self._data[REQUESTER_POSTAL_CODE] = postal_code

    @property
    def requester_region(self):
        return self._data.get(REQUESTER_REGION, None)

    @requester_region.setter
    def requester_region(self, region):
        self._data[REQUESTER_REGION] = region

    @property
    def requester_country(self):
        return self._data.get(REQUESTER_COUNTRY, None)

    @requester_country.setter
    def requester_country(self, country):
        if country not in iso3166.countries_by_alpha3.keys():
            msg = 'Country must have 3 letter and must exist {}'
            raise SeedRequestValidationError(msg.format(country))
        self._data[REQUESTER_COUNTRY] = country

    @property
    def requester_email(self):
        return self._data.get(REQUESTER_EMAIL, None)

    @requester_email.setter
    def requester_email(self, email):
        if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
            raise SeedRequestValidationError('email is malformed {}'.format(email))
        self._data[REQUESTER_EMAIL] = email

    @property
    def request_date(self) -> date:
        return self._data.get(REQUEST_DATE, None)

    @request_date.setter
    def request_date(self, request_date: str):
        if request_date:
            year, month, day = request_date.split('/')
            self._data[REQUEST_DATE] = date(int(year), int(month), int(day))

    @property
    def request_aim(self):
        return self._data.get(REQUEST_AIM, None)

    @request_aim.setter
    def request_aim(self, aim):
        self._data[REQUEST_AIM] = aim

    @property
    def request_comments(self):
        return self._data.get(REQUEST_COMMENTS, None)

    @request_comments.setter
    def request_comments(self, comments):
        self._data[REQUEST_COMMENTS] = comments

    @property
    def requested_accessions(self):
        return self._data.get(REQUESTED_ACCESSIONS, None)

    @requested_accessions.setter
    def requested_accessions(self, accessions):
        self._data[REQUESTED_ACCESSIONS] = accessions

    def _populate_with_instance(self, instance, fields):
        accepted_fields = SEED_REQUEST_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or REQUEST_UID in fields:
            self.request_uid = instance.request_uid
        if fields is None or REQUESTER_NAME in fields:
            self.requester_name = instance.requester_name
        if fields is None or REQUESTER_TYPE in fields:
            self.requester_type = instance.requester_type
        if fields is None or REQUESTER_INSTITUTION in fields:
            self.requester_institution = instance.requester_institution

        if fields is None or REQUESTER_ADDRESS in fields:
            self.requester_address = instance.requester_address
        if fields is None or REQUESTER_CITY in fields:
            self.requester_city = instance.requester_city
        if fields is None or REQUESTER_POSTAL_CODE in fields:
            self.requester_postal_code = instance.requester_postal_code
        if fields is None or REQUESTER_REGION in fields:
            self.requester_region = instance.requester_region
        if fields is None or REQUESTER_COUNTRY in fields:
            self.requester_country = instance.requester_country.code
        if fields is None or REQUESTER_EMAIL in fields:
            self.requester_email = instance.requester_email
        if fields is None or REQUEST_DATE in fields:
            self.request_date = instance.request_date.strftime('%Y/%m/%d')
        if fields is None or REQUEST_AIM in fields:
            self.request_aim = instance.request_aim
        if fields is None or REQUEST_COMMENTS in fields:
            self.request_comments = instance.request_comments

        if fields is None or REQUESTED_ACCESSIONS in fields:
            accessions = []
            for accession_instance in instance.requested_accessions.all():
                accessions.append(
                    {INSTITUTE_CODE: accession_instance.institute.code,
                     GERMPLASM_NUMBER: accession_instance.germplasm_number})
            self.requested_accessions = accessions

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = SEED_REQUEST_CSV_FIELD_CONFS.get(field)['getter']
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


def build_accesion_list(seed_request):
    acce_str = []
    for acc in seed_request.requested_accessions:
        acce_str.append('{}:{}'.format(acc[INSTITUTE_CODE], acc[GERMPLASM_NUMBER]))
    return ';'.join(acce_str)


_SEED_REQUEST_CSV_FIELD_CONFS = [
    {'csv_field_name': 'REQUEST UID', 'getter': lambda x: x.request_uid},
    {'csv_field_name': 'NAME', 'getter': lambda x: x.requester_name},
    {'csv_field_name': 'TYPE', 'getter': lambda x: x.requester_type},
    {'csv_field_name': 'INSTITUTION', 'getter': lambda x: x.requester_institution},
    {'csv_field_name': 'ADDRESS', 'getter': lambda x: x.requester_address},
    {'csv_field_name': 'CITY', 'getter': lambda x: x.requester_city},
    {'csv_field_name': 'POSTAL_CODE', 'getter': lambda x: x.requester_postal_code},
    {'csv_field_name': 'COUNTY', 'getter': lambda x: x.requester_country},
    {'csv_field_name': 'EMAIL', 'getter': lambda x: x.requester_email},
    {'csv_field_name': 'REQUEST_DATE', 'getter': lambda x: x.request_date.strftime('%Y/%m/%d')},
    {'csv_field_name': 'AIM', 'getter': lambda x: x.request_aim},
    {'csv_field_name': 'COMMENTS', 'getter': lambda x: x.request_comments},
    {'csv_field_name': 'ACCESSIONS', 'getter': build_accesion_list},
]
SEED_REQUEST_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _SEED_REQUEST_CSV_FIELD_CONFS])


def create_seed_request_in_db(api_data, user=None, is_public=None):
    # when we are creating
    try:
        struct = SeedRequestStruct(api_data=api_data)
    except SeedRequestValidationError as error:
        raise ValueError(error)

    try:
        country = Country.objects.get(code=struct.requester_country)
    except Country.DoesNotExist:
        raise ValueError('given country does not exist {}'.format(struct.requester_country))
    requests = []
    with transaction.atomic():
        # fo each accession institute one request
        accessions_by_institute = {}
        for accession in struct.requested_accessions:
            institute_code = accession[INSTITUTE_CODE]
            if institute_code not in accessions_by_institute:
                accessions_by_institute[institute_code] = []
            accessions_by_institute[institute_code].append(accession)

        mails = []
        mail_prepare_errors = []

        today = date.today().strftime('%Y%m%d')
        request_uid_num = SeedRequest.objects.filter(request_uid__startswith=today)
        todays_next_id = len(request_uid_num) + 1

        for institute_code, accessions in accessions_by_institute.items():

            seed_request = SeedRequest.objects.create(
                request_uid='{}-{:03d}'.format(today, todays_next_id),
                requester_name=struct.requester_name,
                requester_type=struct.requester_type,
                requester_institution=struct.requester_institution,
                requester_address=struct.requester_address,
                requester_city=struct.requester_city,
                requester_postal_code=struct.requester_postal_code,
                requester_region=struct.requester_region,
                requester_country=country,
                requester_email=struct.requester_email,
                request_date=date.today(),
                request_aim=struct.request_aim,
                request_comments=struct.request_comments)
            todays_next_id += 1

            for accession in accessions:
                try:
                    accession_db = Accession.objects.get(institute__code=accession[INSTITUTE_CODE],
                                                         germplasm_number=accession[GERMPLASM_NUMBER])
                except Accession.DoesNotExist:
                    msg = 'This accession does not exists: {}:{}'
                    msg = msg.format(accession[INSTITUTE_CODE], accession[GERMPLASM_NUMBER])
                    raise ValueError(msg)
                seed_request.requested_accessions.add(accession_db)
            try:
                mails.append(prepare_mail_request(seed_request))
            except RuntimeError as error:
                mail_prepare_errors.append(str(error))
            requests.append(seed_request)

        if mail_prepare_errors:
            raise ValueError(mail_prepare_errors)

        try:
            send_mass_mail(tuple(mails))
        except smtplib.SMTPException as error:
            raise ValueError(error)

    return requests
