import csv
from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.models import (Group, Project, Study)

from vavilov3.permissions import is_user_admin
from vavilov3.views import format_error_message
from vavilov3.entities.study import (StudyStruct, validate_study_data,
                                     StudyValidationError)
from vavilov3.entities.shared import VavilovListSerializer, VavilovSerializer


class StudyMixinSerializer():

    def validate_data(self, data):
        return validate_study_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_study_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_study_in_db(item, user)


class StudyListSerializer(StudyMixinSerializer, VavilovListSerializer):
    pass


class StudySerializer(StudyMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = StudyListSerializer
        Struct = StudyStruct
        ValidationError = StudyValidationError


def create_study_in_db(api_data, user, is_public=None):
    # when we are creating
    try:
        study_struct = StudyStruct(api_data=api_data)
    except StudyValidationError as error:
        print(error)
        raise

    if (study_struct.metadata.group or study_struct.metadata.is_public):
        msg = 'can not set group or is public while creating the study'
        raise ValueError(msg)

    if study_struct.project_name:
        try:
            project = Project.objects.get(name=study_struct.project_name)
        except Project.DoesNotExist:
            msg = '{} does not exist in database'
            msg = msg.format(study_struct.project_name)
            raise ValueError(msg)
    else:
        project = None

    # in the doc we must enter whole document
    if is_public is None:
        is_public = False

    group = user.groups.first()
    study_struct.metadata.is_public = is_public
    study_struct.metadata.group = group.name

    with transaction.atomic():
        try:
            study = Study.objects.create(
                name=study_struct.name,
                description=study_struct.description,
                is_active=study_struct.is_active,
                project=project,
                group=group,
                is_public=is_public,
                data=study_struct.data)
        except IntegrityError:
            msg = 'This study already exists in db: {}'.format(study_struct.name)
            raise ValueError(msg)

    return study


def update_study_in_db(validated_data, instance, user):
    study_struct = StudyStruct(api_data=validated_data)
    if (study_struct.name != instance.name):
        msg = 'Can not change id in an update operation'
        raise ValidationError(format_error_message(msg))

    group_belong_to_user = bool(user.groups.filter(name=study_struct.metadata.group).count())

    if not group_belong_to_user and not is_user_admin(user):
        msg = 'Can not change ownership if group does not belong to you : {}'
        msg = msg.format(study_struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    try:
        group = Group.objects.get(name=study_struct.metadata.group)
    except Group.DoesNotExist:
        msg = 'Provided group does not exist in db: {}'
        msg = msg.format(study_struct.metadata.group)
        raise ValidationError(format_error_message(msg))

    instance.description = study_struct.description
    instance.is_active = study_struct.is_active
    instance.group = group
    instance.is_public = study_struct.metadata.is_public
    instance.data = study_struct.data
    instance.save()
    return instance


def serialize_study_from_csv(fhand):
    reader = csv.DictReader(fhand, delimiter=',')
    fields = reader.fieldnames
    data = []
    for row in reader:
        row = OrderedDict(((field, row[field]) for field in fields))
        study_struct = StudyStruct()
        study_struct.populate_from_csvrow(row)
        data.append(study_struct.get_api_document())
    return data
