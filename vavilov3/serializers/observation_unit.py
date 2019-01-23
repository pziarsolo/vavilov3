from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.models import Study, ObservationUnit, Accession, Plant
from vavilov3.views import format_error_message

from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER
from vavilov3.permissions import is_user_admin

from vavilov3.entities.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.observation_unit import (ObservationUnitStruct,
                                                ObservationUnitValidationError,
                                                validate_observation_unit_data)


class ObservationUnitMixinSerializer():

    def validate_data(self, data):
        return validate_observation_unit_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_observation_unit_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_observation_unit_in_db(item, user)


class ObservationUnitListSerializer(ObservationUnitMixinSerializer,
                                    VavilovListSerializer):
    pass


class ObservationUnitSerializer(ObservationUnitMixinSerializer,
                                VavilovSerializer):

    class Meta:
        list_serializer_class = ObservationUnitListSerializer
        Struct = ObservationUnitStruct
        ValidationError = ObservationUnitValidationError
        metadata_validation_fields = []


def create_observation_unit_in_db(api_data, user=None):
    try:
        struct = ObservationUnitStruct(api_data)
    except ObservationUnitValidationError as error:
        print(error)
        raise

    if struct.metadata.group:
        msg = 'can not set group while creating the observation unit'
        raise ValueError(msg)
    try:
        study = Study.objects.get(name=struct.study)
    except Study.DoesNotExist:
        msg = 'The study has not been added yet to the database: ' + struct.study
        raise ValueError(msg)
    institute_code = struct.accession[INSTITUTE_CODE]
    germplasm_number = struct.accession[GERMPLASM_NUMBER]
    try:
        accession = Accession.objects.get(institute__code=institute_code,
                                          germplasm_number=germplasm_number)
    except Accession.DoesNotExist:
        msg = 'The given accessoin is not in db: {} {}'.format(institute_code,
                                                               germplasm_number)
        raise ValueError(msg)
    study_belongs_to_user = bool(user.groups.filter(name=study.group.name).count())

    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not add observation unit to a study you dont own: {}'
        msg = msg.format(study.group.name)
        raise ValueError(msg)

    with transaction.atomic():
        try:
            observation_unit = ObservationUnit.objects.create(
                name=struct.name,
                accession=accession,
                level=struct.level,
                replicate=struct.replicate,
                study=study)
        except IntegrityError:
            msg = 'This observation unit already exists in db: {}'.format(struct.name)
            raise ValueError(msg)
        if struct.plants:
            _add_plants_to_observation_unit(struct.plants, user, observation_unit)

    return observation_unit


def _add_plants_to_observation_unit(plants, user, observation_unit):
    for plant in plants:
        try:
            plant = Plant.objects.get(name=plant)
            plant_belongs_to_user = bool(user.groups.filter(name=plant.group.name).count())
            if not plant_belongs_to_user and not is_user_admin(user):
                msg = 'Can not add plant you dont own to observation unit: {}'
                msg = msg.format(plant.name)
                raise ValueError(msg)
        except Plant.DoesNotExist:
            msg = 'The given plant does not exist in {} : {}'
            raise ValueError(msg.format(observation_unit.name, plant))
        observation_unit.plant_set.add(plant)


def update_observation_unit_in_db(validated_data, instance, user):
    struct = ObservationUnitStruct(api_data=validated_data)
    if struct.name != instance.name:
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))
    try:
        study = Study.objects.get(name=struct.study)
    except Study.DoesNotExist:
        msg = 'The study has not been added yet to the database: ' + struct.study
        raise ValueError(msg)
    institute_code = struct.accession[INSTITUTE_CODE]
    germplasm_number = struct.accession[GERMPLASM_NUMBER]

    try:
        accession = Accession.objects.get(institute__code=institute_code,
                                          germplasm_number=germplasm_number)
    except Accession.DoesNotExist:
        msg = 'The given accessoin is not in db: {} {}'.format(institute_code,
                                                               germplasm_number)
        raise ValueError(msg)

    study_belongs_to_user = bool(user.groups.filter(name=study.group.name).count())

    if not study_belongs_to_user and not is_user_admin(user):
        msg = 'Can not change ownership if study does not belong to you : {}'
        msg = msg.format(study.group.name)
        raise ValidationError(format_error_message(msg))

    instance.accession = accession
    instance.level = struct.level
    instance.replicate = struct.replicate
    instance.study = study

    instance.save()
    plants = [] if struct.plants is None else struct.plants

    instance.plant_set.clear()
    _add_plants_to_observation_unit(plants, user, instance)

    return instance
