from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from vavilov3_accession.models import (Group, Accession, Institute, DataSource,
                                       Country, Passport, Rank, Taxon)
from vavilov3_accession.entities.accession import (AccessionValidationError,
                                                   AccessionStruct,
                                                   validate_accession_data)
from vavilov3_accession.serializers.shared import DynamicFieldsSerializer
from vavilov3_accession.entities.metadata import (validate_metadata_data,
                                                  MetadataValidationError)
from vavilov3_accession.entities.passport import PassportValidationError


class AccessionSerializer(DynamicFieldsSerializer):

    def to_representation(self, instance):
        accession_struct = AccessionStruct(instance=instance,
                                           fields=self.selected_fields)
        return accession_struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            validate_accession_data(data['data'])
        except AccessionValidationError as error:
            raise ValidationError({'detail': error})
        try:
            validate_metadata_data(data['metadata'])
        except MetadataValidationError as error:
            raise ValidationError({'detail': error})

        return data

    def create(self, validated_data):
        return create_accession_in_db(validated_data)

    def update(self, instance, validated_data):
        return update_accession_in_db(validated_data, instance)


def create_accession_in_db(api_data):
    try:
        accession_struct = AccessionStruct(api_data=api_data)
    except (AccessionValidationError, PassportValidationError) as error:
        print(error)
        raise

    try:
        group = Group.objects.get(name=accession_struct.metadata.group)
    except Group.DoesNotExist:
        msg = '{} does not exist in database'
        raise ValidationError(msg.format(accession_struct.metadata.group))

    try:
        institute = Institute.objects.get(code=accession_struct.institute_code)
    except Institute.DoesNotExist:
        msg = '{} does not exist in database'
        raise ValidationError(msg.format(accession_struct.institute_code))

    with transaction.atomic():
        try:
            accession = Accession.objects.create(
                institute=institute,
                germplasm_number=accession_struct.germplasm_number,
                conservation_status=accession_struct.conservation_status,
                is_available=accession_struct.is_available,
                group=group, is_public=accession_struct.metadata.is_public,
                data=accession_struct.data
                )
        except IntegrityError:
            msg = 'This accession already exists in db: {} {}'
            raise ValidationError(
                msg.format(institute.code, accession_struct.germplasm_number))

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
        data_source = DataSource.objects.get_or_create(
            code=data_source, kind=data_source_kind)[0]
    country = passport_struct.location.country
    if country:
        try:
            country = Country.objects.get(code=country)
        except(BaseException, Country.DoesNotExist):
            print(country)
            raise

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
            raise ValueError('{}: {} does not exist in our database'.format())

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


def update_accession_in_db(validated_data, instance):
    accession_struct = AccessionStruct(api_data=validated_data)
    if (accession_struct.institute_code != instance.institute.code or
            accession_struct.germplasm_number != instance.germplasm_number):
        raise ValidationError('Can not change id in an update operation')

    try:
        group = Group.objects.get(name=accession_struct.metadata.group)
    except Group.DoesNotExist:
        msg = 'Provided group does not exist in db: {}'
        raise ValidationError(msg.format(accession_struct.metadata.group))

    instance.is_available = accession_struct.is_available
    instance.conservation_status = accession_struct.conservation_status
    instance.group = group
    instance.is_public = accession_struct.metadata.is_public
    instance.passports.all().delete()
    for passport_struct in accession_struct.passports:
        _create_passport_in_db(passport_struct, instance)

    instance.save()
    return instance
