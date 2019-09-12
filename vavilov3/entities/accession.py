import csv
from datetime import datetime
from copy import deepcopy
from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.entities.tags import (INSTITUTE_CODE, GERMPLASM_NUMBER,
                                    IS_SAVE_DUPLICATE, IS_AVAILABLE,
                                    CONSTATUS, PASSPORTS, PUID,
                                    VALID_CONSERVATION_STATUSES)
from vavilov3.entities.metadata import Metadata
from vavilov3.entities.passport import (PassportStruct,
                                        validate_passport_data,
                                        PASSPORT_CSV_FIELD_CONFS,
                                        merge_passports)
from vavilov3.models import (Group, Accession, Institute, DataSource,
                             Country, Passport, Rank, Taxon)
from vavilov3.entities.passport import PassportValidationError
from vavilov3.permissions import is_user_admin
from vavilov3.views import format_error_message
from vavilov3.excel import excel_dict_reader
from decimal import InvalidOperation
from vavilov3.id_validator import validate_id


class AccessionValidationError(Exception):
    pass


def validate_accession_data(data):
    if INSTITUTE_CODE not in data:
        raise AccessionValidationError('{} mandatory'.format(INSTITUTE_CODE))
    if GERMPLASM_NUMBER not in data:
        raise AccessionValidationError('{} mandatory'.format(GERMPLASM_NUMBER))

    try:
        validate_id(data[INSTITUTE_CODE])
    except ValueError as msg:
        raise AccessionValidationError(msg)

    try:
        validate_id(data[GERMPLASM_NUMBER])
    except ValueError as msg:
        raise AccessionValidationError(msg)

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
            validate_accession_data(payload)
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
                           CONSTATUS, PASSPORTS, 'genera', 'countries',
                           'longitude', 'latitude']
        if fields is not None and not set(fields).issubset(accepted_fields):
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

        if fields is None or (PASSPORTS in fields or 'latitude' in fields or 'longitude' in fields):
            passports = []
            passport_fields = []
            if fields and 'latitude' in fields:
                passport_fields.append('latitude')
            if fields and 'longitude' in fields:
                passport_fields.append('longitude')

            if not passport_fields:
                passport_fields = None

            for passport_instance in instance.passports.all():
                passport_struct = PassportStruct(instance=passport_instance,
                                                 fields=passport_fields)
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
            passport_field_conf = PASSPORT_CSV_FIELD_CONFS.get(field)
            if not field_conf and not passport_field_conf:
                continue

            if field_conf:
                setter = field_conf['setter']
                try:
                    setter(self, value)
                except ValueError as error:
                    raise AccessionValidationError(error)

            if passport_field_conf:
                passport_setter = passport_field_conf['setter']
                try:
                    passport_setter(_passport, value)
                except ValueError as error:
                    print(error)
                    raise AccessionValidationError(error)
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
     'setter': lambda obj, val: setattr(obj, 'is_available', True if val == 'True' else False)},
]
ACCESSION_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _ACCESSION_CSV_FIELD_CONFS])


def create_accession_in_db(api_data, user, is_public=None):
    # when we are creating
    try:
        accession_struct = AccessionStruct(api_data=api_data)
    except (AccessionValidationError, PassportValidationError) as error:
        print(error)
        raise

    if (accession_struct.metadata.group or accession_struct.metadata.is_public):
        msg = 'can not set group or is public while creating the accession'
        raise ValueError(msg)

    try:
        institute = Institute.objects.get(code=accession_struct.institute_code)
    except Institute.DoesNotExist:
        msg = '{} does not exist in database'
        msg = msg.format(accession_struct.institute_code)
        raise ValueError(msg)

    # in the doc we must enter whole document
    if is_public is None:
        is_public = False
    group = user.groups.first()
    accession_struct.metadata.is_public = is_public
    accession_struct.metadata.group = group.name

    with transaction.atomic():
        try:
            accession = Accession.objects.create(
                institute=institute,
                germplasm_number=accession_struct.germplasm_number,
                conservation_status=accession_struct.conservation_status,
                is_available=accession_struct.is_available,
                group=group,
                is_public=is_public,
                data=accession_struct.data)
        except IntegrityError:
            msg = 'This accession already exists in db: {} {}'
            msg = msg.format(institute.code,
                             accession_struct.germplasm_number)
            raise ValueError(msg)

        for passport_struct in accession_struct.passports:
            try:
                _create_passport_in_db(passport_struct, accession)
            except InvalidOperation:
                msg = '{}:{} longitude or latitude data is wrong- {} {}'
                msg = msg.format(institute.code,
                                 accession_struct.germplasm_number,
                                 passport_struct.longitude,
                                 passport_struct.latitude)
                raise ValueError(msg)

    return accession


def _create_passport_in_db(passport_struct, accession):

    institute_code = passport_struct.institute_code
    germplasm_number = passport_struct.germplasm_number
    institute = Institute.objects.get(code=institute_code)
    data_source = passport_struct.data_source
    data_source_kind = passport_struct.data_source_kind
    if data_source is not None:
        try:
            data_source = DataSource.objects.get_or_create(
                code=data_source, kind=data_source_kind)[0]
        except IntegrityError:
            msg = '{} already in database, it must be defined with a different'
            msg += 'kind'
            raise ValidationError(format_error_message(msg.format(data_source)))
    country = passport_struct.location.country
    if country:
        try:
            country = Country.objects.get(code=country)
        except(BaseException, Country.DoesNotExist):
            raise ValidationError(format_error_message('{} country not in db'))

    biological_status = passport_struct.bio_status
    collection_source = passport_struct.collection_source
    accession_name = passport_struct.germplasm_name
    state = passport_struct.location.state
    province = passport_struct.location.province
    municipality = passport_struct.location.municipality
    location_site = passport_struct.location.site
    crop_name = passport_struct.crop_name

    collecting_institute = passport_struct.collection.institute
    if collecting_institute:
        try:
            collecting_institute = Institute.objects.get(
                code=collecting_institute)
        except Institute.DoesNotExist:
            msg = '{}: {} does not exist in our database'.format(
                passport_struct.germplasm_number,
                passport_struct.institute_code)
            raise ValueError(msg)

    collection_number = passport_struct.collection.number
    collection_field_number = passport_struct.collection.field_number

    if not collection_number and collection_field_number:
        collection_number = collection_field_number

    longitude = passport_struct.location.longitude
    latitude = passport_struct.location.latitude

    pdci = passport_struct.pdci

    passport = Passport.objects.create(institute=institute,
                                       germplasm_number=germplasm_number,
                                       pdci=pdci, country=country,
                                       state=state, province=province,
                                       municipality=municipality,
                                       location_site=location_site,
                                       biological_status=biological_status,
                                       collection_source=collection_source,
                                       latitude=latitude, longitude=longitude,
                                       accession_name=accession_name,
                                       crop_name=crop_name,
                                       collection_number=collection_number,
                                       data_source=data_source,
                                       data=passport_struct.data,
                                       accession=accession)

    add_passport_taxas(passport, passport_struct.taxonomy)
    return passport


def add_passport_taxas(passport, taxonomy):
    for rank, taxon in taxonomy.composed_taxons:
        rank_db = Rank.objects.get(name=rank)
        taxon = Taxon.objects.get_or_create(rank=rank_db, name=taxon)[0]
        taxon.passport_set.add(passport)


def update_accession_in_db(validated_data, instance, user):
    accession_struct = AccessionStruct(api_data=validated_data)
    if (accession_struct.institute_code != instance.institute.code or
            accession_struct.germplasm_number != instance.germplasm_number):
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))

    group_belong_to_user = bool(user.groups.filter(name=accession_struct.metadata.group).count())

    if not group_belong_to_user and not is_user_admin(user):
        msg = 'Can not change ownership if group does not belong to you : {}'
        msg = msg.format(accession_struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    try:
        group = Group.objects.get(name=accession_struct.metadata.group)
    except Group.DoesNotExist:
        msg = 'Provided group does not exist in db: {}'
        msg = msg.format(accession_struct.metadata.group)
        raise ValidationError(format_error_message(msg))
    with transaction.atomic():
        instance.is_available = accession_struct.is_available
        instance.conservation_status = accession_struct.conservation_status
        instance.group = group
        instance.is_public = accession_struct.metadata.is_public
        instance.passports.all().delete()
        for passport_struct in accession_struct.passports:
            _create_passport_in_db(passport_struct, instance)

        instance.save()
        return instance


def serialize_accessions_from_csv(fhand, data_source_code, data_source_kind):
    reader = csv.DictReader(fhand, delimiter=',')
    fields = reader.fieldnames
    data = []
    for row in reader:
        row = OrderedDict(((field, row[field]) for field in fields))
        accession_struct = AccessionStruct()
        accession_struct.populate_from_csvrow(row)
        accession_struct.passports[0].data_source = data_source_code
        accession_struct.passports[0].data_source_kind = data_source_kind
        accession_struct.passports[0].retrieval_date = datetime.now().strftime('%Y-%m-%d')
        data.append(accession_struct.get_api_document())
    return data


def serialize_accessions_from_excel(fhand, data_source_code, data_source_kind):
    data = []
    for row in excel_dict_reader(fhand, values_as_text=True):
        accession_struct = AccessionStruct()
        accession_struct.populate_from_csvrow(row)
        accession_struct.passports[0].data_source = data_source_code
        accession_struct.passports[0].data_source_kind = data_source_kind
        accession_struct.passports[0].retrieval_date = datetime.now().strftime('%Y-%m-%d')
        data.append(accession_struct.get_api_document())
    return data
