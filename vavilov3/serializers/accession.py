import csv
from datetime import datetime
from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework import serializers

from vavilov3.models import (Group, Accession, Institute, DataSource,
                             Country, Passport, Rank, Taxon)
from vavilov3.entities.accession import (AccessionValidationError,
                                         AccessionStruct,
                                         validate_accession_data)
from vavilov3.serializers.shared import DynamicFieldsSerializer
from vavilov3.entities.metadata import (validate_metadata_data,
                                        MetadataValidationError)
from vavilov3.entities.passport import PassportValidationError
from vavilov3.permissions import _user_is_admin
from vavilov3.views import format_error_message


class AccessionListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        errors = []
        instances = []
        group = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            group = request.user.groups.first()

        with transaction.atomic():
            for item in validated_data:
                try:
                    instances.append(create_accession_in_db(item, group))
                except ValueError as error:
                    errors.append(error)

            if errors:
                raise ValidationError(format_error_message(errors))
            else:
                return instances

    def update(self, instance, validated_data):
        instances = []
        errors = []
        with transaction.atomic():
            for instance, payload in zip(instance, validated_data):
                try:
                    instances.append(update_accession_in_db(payload, instance))
                except ValueError as error:
                    errors.append(error)

            if errors:
                raise ValidationError(format_error_message(errors))
            else:
                return instances


class AccessionSerializer(DynamicFieldsSerializer):

    class Meta:
        list_serializer_class = AccessionListSerializer

    def to_representation(self, instance):
        accession_struct = AccessionStruct(instance=instance,
                                           fields=self.selected_fields)
        return accession_struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            validate_accession_data(data['data'])
        except AccessionValidationError as error:
            raise ValidationError(format_error_message(error))
        except MultiValueDictKeyError as error:
            if 'data' in str(error):
                msg = format_error_message('Data key not present')
                raise ValidationError(msg)
            raise ValidationError(format_error_message(error))

        # only validate data updatint, not creating
        if (self.context['request'].method != 'POST'):
            try:
                validate_metadata_data(data['metadata'])
            except MetadataValidationError as error:
                raise ValidationError(format_error_message(error))

        return data

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user.groups.first()
        try:
            return create_accession_in_db(validated_data, user)
        except ValueError as error:
            raise ValidationError(format_error_message(error))

    def update(self, instance, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return update_accession_in_db(validated_data, instance, user)


def create_accession_in_db(api_data, group, is_public=None):
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
            _create_passport_in_db(passport_struct, accession)

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
            raise ValidationError(msg.format(data_source))
    country = passport_struct.location.country
    if country:
        try:
            country = Country.objects.get(code=country)
        except(BaseException, Country.DoesNotExist):
            raise ValidationError('{} country not in db')

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

    if not group_belong_to_user and not _user_is_admin(user):
        msg = 'Can not change ownership if group does not belong to you : {}'
        msg = msg.format(accession_struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    try:
        group = Group.objects.get(name=accession_struct.metadata.group)
    except Group.DoesNotExist:
        msg = 'Provided group does not exist in db: {}'
        msg = msg.format(accession_struct.metadata.group)
        raise ValidationError(format_error_message(msg))

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
