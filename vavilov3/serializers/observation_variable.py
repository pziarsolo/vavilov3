from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.models import ObservationVariable, ObservationDataType, Group
from vavilov3.views import format_error_message
from vavilov3.entities.observation_variable import (
    ObservationVariableStruct, validate_observation_variable_data,
    ObservationVariableValidationError)
from vavilov3.entities.tags import GROUP
from vavilov3.permissions import is_user_admin

from vavilov3.entities.shared import VavilovListSerializer, VavilovSerializer


class ObservationVariableMixinSerializer():

    def validate_data(self, data):
        return validate_observation_variable_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_observation_variable_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_observation_variable_in_db(item, user)


class ObservationVariableListSerializer(ObservationVariableMixinSerializer,
                                        VavilovListSerializer):
    pass


class ObservationVariableSerializer(ObservationVariableMixinSerializer,
                                    VavilovSerializer):

    class Meta:
        list_serializer_class = ObservationVariableListSerializer
        Struct = ObservationVariableStruct
        ValidationError = ObservationVariableValidationError
        metadata_validation_fields = [GROUP]


def create_observation_variable_in_db(api_data, user):
    try:
        struct = ObservationVariableStruct(api_data)
    except ObservationVariableValidationError as error:
        print(error)
        raise

    if (struct.metadata.group):
        msg = 'can not set group while creating the observation variable'
        raise ValueError(msg)
    try:
        data_type = ObservationDataType.objects.get(name=struct.data_type)
    except ObservationDataType.DoesNotExist:
        raise ValidationError('data type not valid: ' + struct.data_type)

    group = user.groups.first()
    struct.metadata.group = group.name

    with transaction.atomic():
        try:
            observation_variable = ObservationVariable.objects.create(
                name=struct.name,
                description=struct.description,
                trait=struct.trait,
                method=struct.method,
                group=group,
                data_type=data_type,
                unit=struct.unit)
        except IntegrityError:
            msg = 'This observation variable already exists in db: {}'.format(struct.name)
            raise ValueError(msg)

    return observation_variable


def update_observation_variable_in_db(validated_data, instance, user):
    struct = ObservationVariableStruct(api_data=validated_data)
    if struct.name != instance.name:
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))

    group_belong_to_user = bool(user.groups.filter(name=struct.metadata.group).count())

    if not group_belong_to_user and not is_user_admin(user):
        msg = 'Can not change ownership if group does not belong to you : {}'
        msg = msg.format(struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    try:
        group = Group.objects.get(name=struct.metadata.group)
    except Group.DoesNotExist:
        msg = 'Provided group does not exist in db: {}'
        msg = msg.format(struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    instance.description = struct.description
    instance.trait = struct.trait
    instance.group = group
    instance.method = struct.method
    instance.unit = struct.unit
    if struct.data_type != instance.data_type.name:
        try:
            instance.data_type = ObservationDataType.objects.get(name=struct.data_type)
        except ObservationDataType.DoesNotExist:
            msg = 'data type not valid: ' + struct.data_type
            raise ValidationError(format_error_message(msg))

    instance.save()
    return instance
