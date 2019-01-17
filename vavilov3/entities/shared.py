import csv
from collections import OrderedDict

from django.db import transaction
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError

from vavilov3.views import format_error_message
from vavilov3.serializers.shared import DynamicFieldsSerializer
from vavilov3.entities.metadata import (validate_metadata_data,
                                        MetadataValidationError)


class VavilovListSerializer(serializers.ListSerializer):

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
                    instances.append(self.create_item_in_db(item, group))
                except ValueError as error:
                    errors.append(error)

            if errors:
                raise ValidationError(format_error_message(errors))
            else:
                return instances

    def update(self, instance, validated_data):
        instances = []
        errors = []
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        with transaction.atomic():
            for instance, payload in zip(instance, validated_data):
                try:
                    instances.append(self.update_item_in_db(payload, instance, user))
                except ValueError as error:
                    errors.append(error)

            if errors:
                raise ValidationError(format_error_message(errors))
            else:
                return instances

    def update_item_in_db(self, payload, instance, user):
        raise NotImplemented()

    def create_item_in_db(self, item, group):
        raise NotImplemented()


class VavilovSerializer(DynamicFieldsSerializer):

    def to_representation(self, instance):
        struct = self.Meta.Struct(instance=instance,
                                  fields=self.selected_fields)
        return struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            self.validate_data(data['data'])
        except self.Meta.ValidationError as error:
            raise ValidationError(format_error_message(error))
        except MultiValueDictKeyError as error:
            if 'data' in str(error):
                msg = format_error_message('Data key not present')
                raise ValidationError(msg)
            raise ValidationError(format_error_message(error))

        # only validate data updatint, not creating
        if (self.context['request'].method != 'POST'):
            try:
                try:
                    fields_to_validate = self.Meta.metadata_validation_fields
                except AttributeError:
                    fields_to_validate = None

                validate_metadata_data(data['metadata'],
                                       fields_to_validate=fields_to_validate)
            except MetadataValidationError as error:
                raise ValidationError(format_error_message(error))

        return data

    def validate_data(self, data):
        raise NotImplementedError()

    def update_item_in_db(self, payload, instance, user):
        raise NotImplementedError()

    def create_item_in_db(self, item, group):
        raise NotImplementedError()

    def create(self, validated_data):
        group = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            group = request.user.groups.first()
        try:
            return self.create_item_in_db(validated_data, group)
        except ValueError as error:
            raise ValidationError(format_error_message(error))

    def update(self, instance, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return self.update_item_in_db(validated_data, instance, user)


def serialize_entity_from_csv(fhand, Struct):
    reader = csv.DictReader(fhand, delimiter=',')
    fields = reader.fieldnames
    data = []
    for row in reader:
        row = OrderedDict(((field, row[field]) for field in fields))
        study_struct = Struct()
        study_struct.populate_from_csvrow(row)
        data.append(study_struct.get_api_document())
    return data
