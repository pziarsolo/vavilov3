from copy import deepcopy
from collections import OrderedDict

from django.db.utils import IntegrityError
from django.db import transaction

from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.views import format_error_message
from vavilov3.entities.tags import (OBSERVATION_VARIABLE_NAME, TRAIT,
                                    OBSERVATION_VARIABLE_DESCRIPTION, METHOD,
                                    DATA_TYPE, SCALE)
from vavilov3.models import Group, ObservationVariable, Scale, Trait
from vavilov3.permissions import is_user_admin


class ObservationVariableValidationError(Exception):
    pass


OBSERVATION_VARIABLE_ALLOWED_FIELDS = [OBSERVATION_VARIABLE_NAME,
                                       TRAIT, OBSERVATION_VARIABLE_DESCRIPTION,
                                       METHOD, DATA_TYPE, SCALE]
MANDATORY_FIELDS = [OBSERVATION_VARIABLE_NAME, TRAIT,
                    OBSERVATION_VARIABLE_DESCRIPTION, METHOD]


def validate_observation_variable_data(data):
    for mandatory_field in MANDATORY_FIELDS:
        if mandatory_field not in data:
            raise ObservationVariableValidationError('{} mandatory'.format(mandatory_field))

    not_allowed_fields = set(data.keys()).difference(OBSERVATION_VARIABLE_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise ObservationVariableValidationError(msg)


class ObservationVariableStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}
            self._metadata = Metadata()

        elif api_data:
            payload = deepcopy(api_data['data'])
            self._data = payload
            self._metadata = Metadata(api_data['metadata'])

        elif instance:
            self._data = {}
            self._metadata = Metadata()
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        return _data

    def get_api_document(self):
        return {'data': self.data,
                'metadata': self.metadata.data}

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    @property
    def name(self):
        return self._data[OBSERVATION_VARIABLE_NAME]

    @name.setter
    def name(self, name):
        self._data[OBSERVATION_VARIABLE_NAME] = name

    @property
    def description(self):
        return self._data[OBSERVATION_VARIABLE_DESCRIPTION]

    @description.setter
    def description(self, description):
        self._data[OBSERVATION_VARIABLE_DESCRIPTION] = description

    @property
    def trait(self):
        return self._data.get(TRAIT, None)

    @trait.setter
    def trait(self, trait):
        self._data[TRAIT] = trait

    @property
    def method(self):
        return self._data[METHOD]

    @method.setter
    def method(self, method: str):
        if method:
            self._data[METHOD] = method

    @property
    def data_type(self) -> str:
        return self._data[DATA_TYPE]

    @data_type.setter
    def data_type(self, data_type: str):
        if data_type:
            self._data[DATA_TYPE] = data_type

    @property
    def scale(self):
        return self._data.get(SCALE, None)

    @scale.setter
    def scale(self, scale):
        if scale:
            self._data[SCALE] = scale

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.group.name
        accepted_fields = OBSERVATION_VARIABLE_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or OBSERVATION_VARIABLE_NAME in fields:
            self.name = instance.name
        if fields is None or OBSERVATION_VARIABLE_DESCRIPTION in fields:
            self.description = instance.description
        if fields is None or TRAIT in fields:
            self.trait = instance.trait.name
        if fields is None or METHOD in fields:
            self.method = instance.method

        if fields is None or SCALE in fields:
            self.scale = instance.scale.name

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = OBSERVATION_VARIABLE_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

    def populate_from_csvrow(self, row):

        for field, value in row.items():
            if not value:
                continue
            field_conf = OBSERVATION_VARIABLE_CSV_FIELD_CONFS.get(field)

            if field_conf:
                setter = field_conf['setter']
                setter(self, value)


_OBSERVATION_VARIABLE_CSV_FIELD_CONFS = [
    {'csv_field_name': 'NAME', 'getter': lambda x: x.name,
     'setter': lambda obj, val: setattr(obj, 'name', val)},
    {'csv_field_name': 'DESCRIPTION', 'getter': lambda x: x.description,
     'setter': lambda obj, val: setattr(obj, 'description', val)},
    {'csv_field_name': 'TRAIT', 'getter': lambda x: x.trait,
     'setter': lambda obj, val: setattr(obj, 'trait', val)},
    {'csv_field_name': 'METHOD', 'getter': lambda x: x.method,
     'setter': lambda obj, val: setattr(obj, 'method', val)},
    {'csv_field_name': 'DATA_TYPE', 'getter': lambda x: x.data_type,
     'setter': lambda obj, val: setattr(obj, 'data_type', val)},
    {'csv_field_name': 'UNIT', 'getter': lambda x: x.unit,
     'setter': lambda obj, val: setattr(obj, 'unit', val)},
]
OBSERVATION_VARIABLE_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _OBSERVATION_VARIABLE_CSV_FIELD_CONFS])


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
        scale = Scale.objects.get(name=struct.scale)
    except Scale.DoesNotExist:
        raise ValidationError('Scale not valid: ' + struct.scale)
    try:
        trait = Trait.objects.get(name=struct.trait)
    except Trait.DoesNotExist:
        raise ValidationError('Trait not valid: ' + struct.scale)

    group = user.groups.first()
    struct.metadata.group = group.name

    with transaction.atomic():
        try:
            observation_variable = ObservationVariable.objects.create(
                name=struct.name,
                description=struct.description,
                trait=trait,
                method=struct.method,
                group=group,
                scale=scale)
        except IntegrityError as error:
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
    try:
        scale = Scale.objects.get(name=struct.scale)
    except Scale.DoesNotExist:
        raise ValidationError('Scale not valid: ' + struct.scale)
    try:
        trait = Trait.objects.get(name=struct.trait)
    except Trait.DoesNotExist:
        raise ValidationError('Trait not valid: ' + struct.scale)

    instance.description = struct.description
    instance.trait = trait
    instance.group = group
    instance.method = struct.method
    instance.scale = scale

    instance.save()
    return instance
