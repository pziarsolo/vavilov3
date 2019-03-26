import csv
from collections import OrderedDict

from django.db import transaction
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework.fields import empty
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from vavilov3.views import format_error_message
from vavilov3.entities.metadata import (validate_metadata_data,
                                        MetadataValidationError)
from vavilov3.tasks import (create_accessions_task, add_task_to_user,
                            create_accessionsets_task,
                            create_observation_units_task,
                            create_plants_task,
                            create_observation_variables_task,
                            create_studies_task, create_observations_task,
                            create_trait_task, wait_func, create_scale_task,
                            create_observation_images_task)


class DynamicFieldsSerializer(serializers.Serializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsSerializer, self).__init__(*args, **kwargs)
        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            self.selected_fields = fields
        else:
            self.selected_fields = None


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class VavilovListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
#         async_result = wait_func.delay(30)
#         add_task_to_user(user, async_result)
#         return async_result
        if self.data_type == 'accession':
            async_result = create_accessions_task.delay(validated_data,
                                                        user.username)
        elif self.data_type == 'accessionset':
            async_result = create_accessionsets_task.delay(validated_data,
                                                           user.username)
        elif self.data_type == 'study':
            async_result = create_studies_task.delay(validated_data,
                                                     user.username)
        elif self.data_type == 'observation_variable':
            async_result = create_observation_variables_task.delay(validated_data,
                                                                   user.username)
        elif self.data_type == 'observation_unit':
            async_result = create_observation_units_task.delay(validated_data,
                                                               user.username)
        elif self.data_type == 'plant':
            async_result = create_plants_task.delay(validated_data,
                                                    user.username)
        elif self.data_type == 'observation':
            conf = self.context['view'].conf
            async_result = create_observations_task.delay(validated_data,
                                                          user.username,
                                                          conf)
        elif self.data_type == 'observation_image':
            conf = self.context['view'].conf
            async_result = create_observation_images_task.delay(validated_data,
                                                                user.username,
                                                                conf)
        elif self.data_type == 'trait':
            async_result = create_trait_task.delay(validated_data, user.username)
        elif self.data_type == 'scale':
            async_result = create_scale_task.delay(validated_data, user.username)
        else:
            msg = 'We dont have a create task for the given data type {}'
            raise NotImplementedError(msg.format(self.data_type))

        add_task_to_user(user, async_result)
        return async_result

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

    def create_item_in_db(self, item, user):
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
                if fields_to_validate:
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
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        try:
            return self.create_item_in_db(validated_data, user)
        except ValueError as error:
            raise ValidationError(format_error_message(error))

    def update(self, instance, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        try:
            return self.update_item_in_db(validated_data, instance, user)
        except ValueError as error:
            raise ValidationError(format_error_message(error))


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
