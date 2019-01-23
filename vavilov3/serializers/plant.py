from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.models import Group, Plant
from vavilov3.views import format_error_message
from vavilov3.entities.tags import GROUP
from vavilov3.permissions import is_user_admin
from vavilov3.entities.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.plant import (PlantStruct, PlantValidationError,
                                     validate_plant_data)


class PlantMixinSerializer():

    def validate_data(self, data):
        return validate_plant_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_plant_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_plant_in_db(item, user)


class PlantListSerializer(PlantMixinSerializer, VavilovListSerializer):
    pass


class PlantSerializer(PlantMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = PlantListSerializer
        Struct = PlantStruct
        ValidationError = PlantValidationError
        metadata_validation_fields = [GROUP]


def create_plant_in_db(api_data, user):
    try:
        struct = PlantStruct(api_data)
    except PlantValidationError as error:
        print(error)
        raise

    if (struct.metadata.group):
        msg = 'can not set group while creating the plant'
        raise ValueError(msg)

    group = user.groups.first()
    struct.metadata.group = group.name

    with transaction.atomic():
        try:
            plant = Plant.objects.create(name=struct.name,
                                         group=group,
                                         x=struct.x,
                                         y=struct.y,
                                         block_number=struct.block_number,
                                         entry_number=struct.entry_number,
                                         plant_number=struct.plant_number,
                                         plot_number=struct.plot_number)
        except IntegrityError:
            msg = 'This plant already exists in db: {}'.format(struct.name)
            raise ValueError(msg)

    return plant


def update_plant_in_db(validated_data, instance, user):
    struct = PlantStruct(api_data=validated_data)
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

    instance.x = struct.x
    instance.y = struct.y
    instance.group = group
    instance.block_number = struct.block_number
    instance.entry_number = struct.entry_number
    instance.plant_number = struct.plant_number
    instance.plot_number = struct.plot_number
    instance.save()
    return instance
