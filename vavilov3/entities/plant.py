from copy import deepcopy
from collections import OrderedDict

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.entities.metadata import Metadata
from vavilov3.views import format_error_message
from vavilov3.entities.tags import (PLANT_NAME, PLANT_X, PLANT_Y, BLOCK_NUMBER,
                                    ENTRY_NUMBER, PLANT_NUMBER, PLOT_NUMBER)
from vavilov3.models import Group, Plant
from vavilov3.permissions import is_user_admin


class PlantValidationError(Exception):
    pass


PLANT_ALLOWED_FIELDS = [PLANT_NAME, PLANT_X, PLANT_Y, BLOCK_NUMBER, ENTRY_NUMBER,
                        PLANT_NUMBER, PLOT_NUMBER]


def validate_plant_data(data):
    if PLANT_NAME not in data:
        raise PlantValidationError('{} mandatory'.format(PLANT_NAME))

    not_allowed_fields = set(data.keys()).difference(PLANT_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise PlantValidationError(msg)


class PlantStruct():

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
        return self._data[PLANT_NAME]

    @name.setter
    def name(self, name):
        self._data[PLANT_NAME] = name

    @property
    def x(self):
        return self._data.get(PLANT_X, None)

    @x.setter
    def x(self, x):
        self._data[PLANT_X] = x

    @property
    def y(self):
        return self._data.get(PLANT_Y, None)

    @y.setter
    def y(self, y):
        self._data[PLANT_Y] = y

    @property
    def block_number(self):
        return self._data.get(BLOCK_NUMBER, None)

    @block_number.setter
    def block_number(self, block_number):
        self._data[BLOCK_NUMBER] = block_number

    @property
    def entry_number(self):
        return self._data.get(ENTRY_NUMBER, None)

    @entry_number.setter
    def entry_number(self, entry_number):
        self._data[ENTRY_NUMBER] = entry_number

    @property
    def plant_number(self):
        return self._data.get(PLANT_NUMBER, None)

    @plant_number.setter
    def plant_number(self, plant_number):
        self._data[PLANT_NUMBER] = plant_number

    @property
    def plot_number(self):
        return self._data.get(PLOT_NUMBER, None)

    @plot_number.setter
    def plot_number(self, plot_number):
        self._data[PLOT_NUMBER] = plot_number

    def _populate_with_instance(self, instance, fields):
        self.metadata.group = instance.group.name
        accepted_fields = PLANT_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if (fields is None or PLANT_NAME in fields) and instance.name is not None:
            self.name = instance.name
        if (fields is None or PLANT_X in fields) and instance.x is not None:
            self.x = instance.x
        if (fields is None or PLANT_Y in fields) and instance.y is not None:
            self.y = instance.y
        if (fields is None or BLOCK_NUMBER in fields) and instance.block_number is not None:
            self.block_number = instance.block_number
        if (fields is None or ENTRY_NUMBER in fields) and instance.entry_number is not None:
            self.entry_number = instance.entry_number
        if (fields is None or PLANT_NUMBER in fields) and instance.plant_number is not None:
            self.plant_number = instance.plant_number
        if (fields is None or PLOT_NUMBER in fields) and instance.plot_number is not None:
            self.plot_number = instance.plot_number

    def to_list_representation(self, fields):
        items = []
        for field in fields:
            getter = PLANT_CSV_FIELD_CONFS.get(field)['getter']
            items.append(getter(self))
        return items

    def populate_from_csvrow(self, row):

        for field, value in row.items():
            if not value:
                continue
            field_conf = PLANT_CSV_FIELD_CONFS.get(field)

            if field_conf:
                setter = field_conf['setter']
                setter(self, value)


_PLANT_CSV_FIELD_CONFS = [
    {'csv_field_name': 'NAME', 'getter': lambda x: x.name,
     'setter': lambda obj, val: setattr(obj, 'name', val)},
    {'csv_field_name': 'X', 'getter': lambda x: x.x,
     'setter': lambda obj, val: setattr(obj, 'x', val)},
    {'csv_field_name': 'Y', 'getter': lambda x: x.y,
     'setter': lambda obj, val: setattr(obj, 'y', val)},
    {'csv_field_name': 'BLOCK_NUMBER', 'getter': lambda x: x.block_number,
     'setter': lambda obj, val: setattr(obj, 'block_number', val)},
    {'csv_field_name': 'ENTRY_NUMBER', 'getter': lambda x: x.entry_number,
     'setter': lambda obj, val: setattr(obj, 'entry_number', val)},
    {'csv_field_name': 'PLANT_NUMBER', 'getter': lambda x: x.plant_number,
     'setter': lambda obj, val: setattr(obj, 'plant_number', val)},
    {'csv_field_name': 'PLOT_NUMBER', 'getter': lambda x: x.plot_number,
     'setter': lambda obj, val: setattr(obj, 'plot_number', val)},
]
PLANT_CSV_FIELD_CONFS = OrderedDict([(f['csv_field_name'], f) for f in _PLANT_CSV_FIELD_CONFS])


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
