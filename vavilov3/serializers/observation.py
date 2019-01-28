import pytz
from datetime import datetime

from django.db import transaction
from django.db.utils import IntegrityError
from django.conf.global_settings import TIME_ZONE

from rest_framework.exceptions import ValidationError

from vavilov3.models import ObservationVariable, Observation, ObservationUnit
from vavilov3.views import format_error_message
from vavilov3.permissions import is_user_admin
from vavilov3.entities.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.observation import (ObservationValidationError,
                                           validate_observation_data,
                                           ObservationStruct)
from vavilov3.conf.settings import DATETIME_FORMAT
from rest_framework.fields import empty


class ObservationMixinSerializer():

    def validate_data(self, data):
        return validate_observation_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_observation_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_observation_in_db(item, user)


class ObservationListSerializer(ObservationMixinSerializer,
                                VavilovListSerializer):
    pass


class ObservationSerializer(ObservationMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = ObservationListSerializer
        Struct = ObservationStruct
        ValidationError = ObservationValidationError

    def run_validation(self, data=empty):
        try:
            self.validate_data(data)
        except self.Meta.ValidationError as error:
            raise ValidationError(format_error_message(error))
        return data


def _get_or_create_observation_unit(struct):
    try:
        observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
    except ObservationUnit.DoesNotExist:
        msg = 'This observation Unit {} does not exist in db'
        msg = msg.format(struct.observation_unit)
        raise ValueError(msg)
    return observation_unit


def get_datetime_from_strdate(str_date):
    if not str_date:
        return None
    datetime.strftime(str_date, "")


def create_observation_in_db(api_data, user):
    try:
        struct = ObservationStruct(api_data)
    except ObservationValidationError as error:
        print(error)
        raise
    try:
        observation_variable = ObservationVariable.objects.get(name=struct.observation_variable)
    except ObservationVariable.DoesNotExist:
        msg = 'Observation variable {} does not exist in db'
        msg = msg.format(struct.observation_variable)
        raise ValueError(msg)

    observation_unit = _get_or_create_observation_unit(struct)
    study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())

    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not add observation unit to a study you dont own: {}'
        msg = msg.format(observation_unit.study.group.name)
        raise ValueError(msg)
    if struct.creation_time:
        timezone = pytz.timezone(TIME_ZONE)
        creation_time = timezone.localize(datetime.strptime(struct.creation_time,
                                                            DATETIME_FORMAT))
    else:
        creation_time = None

    with transaction.atomic():
        try:
            observation = Observation.objects.create(
                observation_variable=observation_variable,
                observation_unit=observation_unit,
                value=struct.value,
                observer=struct.observer,
                creation_time=creation_time)
        except IntegrityError:
            msg = 'This observation variable already exists in db: {}'.format(struct.observation_id)
            raise ValueError(msg)

    return observation


def update_observation_in_db(validated_data, instance, user):
    struct = ObservationStruct(api_data=validated_data)
    if struct.observation_id != instance.observation_id:
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))
    try:
        observation_variable = ObservationVariable.objects.get(name=struct.observation_variable)
    except ObservationVariable.DoesNotExist:
        msg = 'Observation variable {} does not exist in db'
        msg = msg.format(struct.observation_variable)
        raise ValueError(msg)
    try:
        observation_unit = ObservationUnit.objects.get(name=struct.observation_unit)
    except ObservationUnit.DoesNotExist:
        msg = 'Observation unit {} does not exist in db'
        msg = msg.format(struct.observation_unit)
        raise ValueError(msg)

    study_belongs_to_user = bool(user.groups.filter(name=observation_unit.study.group.name).count())
    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not change observation unit because this is in a study you dont own: {}'
        msg = msg.format(observation_unit.study.name)
        raise ValueError(msg)

    if struct.creation_time:
        timezone = pytz.timezone(TIME_ZONE)
        creation_time = timezone.localize(datetime.strptime(struct.creation_time,
                                                            DATETIME_FORMAT))
    else:
        creation_time = None

    instance.observation_variable = observation_variable
    instance.observation_unit = observation_unit
    instance.value = struct.value
    instance.observer = struct.observer
    instance.creation_time = creation_time

    instance.save()
    return instance
