from django.db.utils import IntegrityError

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError

from vavilov3_accession.models import Institute, Group
from vavilov3_accession.serializers.metadata import MetadataSerializer
from vavilov3_accession.serializers.shared import DynamicFieldsSerializer
from vavilov3_accession.entities.institute import (InstituteStruct,
                                                   InstituteValidationError,
                                                   validate_institute_data)
from vavilov3_accession.entities.metadata import (validate_metadata_data,
                                                  MetadataValidationError)


class InstituteSerializer(DynamicFieldsSerializer):
    metadata = MetadataSerializer()
    code = serializers.CharField()
    name = serializers.CharField()

    def to_representation(self, instance):
        institute_struct = InstituteStruct(instance=instance,
                                           fields=self.selected_fields)
        return institute_struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            validate_institute_data(data['data'])
        except InstituteValidationError as error:
            raise ValidationError({'detail': error})
        try:
            validate_metadata_data(data['metadata'])
        except MetadataValidationError as error:
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

    group = Group.objects.get(name=institute_struct.metadata.group)
    try:
        institute = Institute.objects.create(
            code=institute_struct.institute_code,
            name=institute_struct.institute_name,
            group=group,
            is_public=institute_struct.metadata.is_public,
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

    try:
        group = Group.objects.get(name=institute_struct.metadata.group)
    except Group.DoesNotExist:
        raise ValidationError('{} group does not exist'.format(
            institute_struct.metadata.group))

    instance.name = institute_struct.institute_name
    instance.group = group
    instance.is_public = institute_struct.metadata.is_public
    instance.data = institute_struct.data
    instance.save()

    return instance
