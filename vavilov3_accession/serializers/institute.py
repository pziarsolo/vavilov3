from django.db.utils import IntegrityError

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError

from vavilov3_accession.serializers.shared import DynamicFieldsSerializer
from vavilov3_accession.entities.institute import (InstituteStruct,
                                                   InstituteValidationError,
                                                   validate_institute_data)
from vavilov3_accession.models import Institute
from vavilov3_accession.views import format_error_message
from django.db import transaction
import csv
from _collections import OrderedDict


class InstituteListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        errors = []
        instances = []

        with transaction.atomic():
            for item in validated_data:
                try:
                    instances.append(create_institute_in_db(item))
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
                    instances.append(update_institute_in_db(payload, instance))
                except ValueError as error:
                    errors.append(error)
            if errors:
                raise ValidationError(format_error_message(errors))
            else:
                return instances


class InstituteSerializer(DynamicFieldsSerializer):
    code = serializers.CharField()
    name = serializers.CharField()

    class Meta:
        list_serializer_class = InstituteListSerializer

    def to_representation(self, instance):
        institute_struct = InstituteStruct(instance=instance,
                                           fields=self.selected_fields)
        return institute_struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            validate_institute_data(data)
        except InstituteValidationError as error:
            raise ValidationError(format_error_message(error))
        return data

    def create(self, validated_data):
        try:
            return create_institute_in_db(validated_data)
        except ValueError as error:
            raise ValidationError(format_error_message(error))

    def update(self, instance, validated_data):
        try:
            return update_institute_in_db(validated_data, instance)
        except ValueError as error:
            raise ValidationError(format_error_message(error))


def create_institute_in_db(api_data):
    try:
        institute_struct = InstituteStruct(api_data)
    except InstituteValidationError as error:
        print(error)
        raise

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


def serialize_institute_from_csv(fhand):
    reader = csv.DictReader(fhand, delimiter=',')
    fields = reader.fieldnames
    data = []
    for row in reader:
        row = OrderedDict(((field, row[field]) for field in fields))
        institute_struct = InstituteStruct()
        institute_struct.populate_from_csvrow(row)
        data.append(institute_struct.get_api_document())
    return data
