import csv
from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework import serializers

from vavilov3_accession.models import (Institute, AccessionSet, Accession)
from vavilov3_accession.serializers.shared import DynamicFieldsSerializer
from vavilov3_accession.entities.metadata import (validate_metadata_data,
                                                  MetadataValidationError)

from vavilov3_accession.entities.accessionset import (
    AccessionSetStruct, AccessionSetValidationError,
    validate_accessionset_data)
from vavilov3_accession.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER
from vavilov3_accession.views import format_error_message


class AccessionSetListSerializer(serializers.ListSerializer):

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
                    instances.append(create_accessionset_in_db(item, group))
                except ValueError as error:
                    errors.append(error)

            if errors:
                raise ValidationError(format_error_message(errors))
            else:
                return instances

#     def update(self, instance, validated_data):
#         instances = []
#         for instance, payload in zip(instance, validated_data):
#             instances.append(update_accession_in_db(payload, instance))
#         return instances


class AccessionSetSerializer(DynamicFieldsSerializer):

    class Meta:
        list_serializer_class = AccessionSetListSerializer

    def to_representation(self, instance):
        accessionset_struct = AccessionSetStruct(instance=instance,
                                                 fields=self.selected_fields)
        return accessionset_struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            validate_accessionset_data(data['data'])
        except AccessionSetValidationError as error:
            raise ValidationError(format_error_message(error))
        except MultiValueDictKeyError as error:
            if 'data' in str(error):
                msg = format_error_message('data key not present')
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
            return create_accessionset_in_db(validated_data, user)
        except ValueError as error:
            raise ValidationError(format_error_message(error))

#     def update(self, instance, validated_data):
#         user = None
#         request = self.context.get("request")
#         if request and hasattr(request, "user"):
#             user = request.user
#         return update_accessionset_in_db(validated_data, instance, user)


def create_accessionset_in_db(api_data, group, is_public=None):
    # when we are creating
    try:
        accessionset_struct = AccessionSetStruct(api_data=api_data)
    except AccessionSetValidationError as error:
        print(error)
        raise

    if (accessionset_struct.metadata.group or accessionset_struct.metadata.is_public):
        msg = 'can not set group or is public while creating the accession'
        raise ValueError(msg)

    try:
        institute = Institute.objects.get(code=accessionset_struct.institute_code)
    except Institute.DoesNotExist:
        msg = '{} does not exist in database'
        raise ValueError(msg.format(accessionset_struct.institute_code))

    # in the doc we must enter whole document
    if is_public is None:
        is_public = False
    accessionset_struct.metadata.is_public = is_public
    accessionset_struct.metadata.group = group.name

    with transaction.atomic():
        try:
            accessionset = AccessionSet.objects.create(
                institute=institute,
                accessionset_number=accessionset_struct.accessionset_number,
                group=group,
                is_public=is_public,
                data=accessionset_struct.data)
        except IntegrityError:
            msg = 'This accessionset already exists in db: {} {}'
            raise ValueError(
                msg.format(institute.code,
                           accessionset_struct.accessionset_number))
        for accession in accessionset_struct.accessions:
            try:
                accession_instance = Accession.objects.get(
                    institute__code=accession[INSTITUTE_CODE],
                    germplasm_number=accession[GERMPLASM_NUMBER])
            except Accession.DoesNotExist:
                msg = "{}: accession not found {}:{}"
                msg = msg.format(accessionset_struct.accessionset_number,
                                 accession[INSTITUTE_CODE],
                                 accession[GERMPLASM_NUMBER])
                raise ValueError(msg)
            if accession_instance:
                accessionset.accessions.add(accession_instance)

    return accessionset


def serialize_accessionsets_from_csv(fhand):
    reader = csv.DictReader(fhand, delimiter=',')
    fields = reader.fieldnames
    data = []
    for row in reader:
        row = OrderedDict(((field, row[field]) for field in fields))
        accessionset_struct = AccessionSetStruct()
        accessionset_struct.populate_from_csvrow(row)
        data.append(accessionset_struct.get_api_document())
    return data
