from django.db.utils import IntegrityError

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError

from vavilov3_accession.serializers.shared import DynamicFieldsSerializer
from vavilov3_accession.entities.institute import (InstituteStruct,
                                                   InstituteValidationError,
                                                   validate_institute_data)
from vavilov3_accession.models import Institute


class InstituteSerializer(DynamicFieldsSerializer):
    code = serializers.CharField()
    name = serializers.CharField()

    def to_representation(self, instance):
        institute_struct = InstituteStruct(instance=instance,
                                           fields=self.selected_fields)
        return institute_struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            validate_institute_data(data)
        except InstituteValidationError as error:
            raise ValidationError({'detail': error})
        return data

    def create(self, validated_data):
        return create_institute_in_db(validated_data)

    def update(self, instance, validated_data):
        return update_institute_in_db(validated_data, instance)


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
        raise ValidationError({'detail': msg})
    return institute


def update_institute_in_db(api_data, instance):
    try:
        institute_struct = InstituteStruct(api_data)
    except InstituteValidationError as error:
        raise ValidationError(error)

    if institute_struct.institute_code != instance.code:
        raise ValidationError('Can not change id in an update operation')

    instance.name = institute_struct.institute_name
    instance.data = institute_struct.data
    instance.save()

    return instance
