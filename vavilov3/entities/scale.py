from copy import deepcopy

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.entities.tags import (SCALE_NAME, SCALE_DESCRIPTION,
                                    SCALE_DATA_TYPE, SCALE_DECIMAL_PLACES,
                                    SCALE_MIN, SCALE_MAX, SCALE_VALID_VALUES)
from vavilov3.views import format_error_message
from vavilov3.models import ScaleDataType, Scale, ScaleCategory

SCALE_ALLOWED_FIELDS = (SCALE_NAME, SCALE_DESCRIPTION, SCALE_DATA_TYPE,
                        SCALE_DECIMAL_PLACES, SCALE_MIN, SCALE_MAX,
                        SCALE_VALID_VALUES)


class ScaleValidationError(Exception):
    pass


MANDATORY_FIELDS = [SCALE_NAME, SCALE_DESCRIPTION, SCALE_DATA_TYPE]


def validate_scale_data(data):
    for mandatory_field in MANDATORY_FIELDS:
        if mandatory_field not in data:
            raise ScaleValidationError('{} mandatory'.format(mandatory_field))

    not_allowed_fields = set(data.keys()).difference(SCALE_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise ScaleValidationError(msg)
    return data


class ScaleStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}

        elif api_data:
            payload = deepcopy(api_data)
            validate_scale_data(payload)
            self._data = payload

        elif instance:
            self._data = {}
            self._populate_with_instance(instance, fields)

    @property
    def data(self):
        _data = deepcopy(self._data)
        return _data

    def get_api_document(self):
        return self.data

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    @property
    def name(self):
        return self._data[SCALE_NAME]

    @name.setter
    def name(self, name):
        self._data[SCALE_NAME] = name

    @property
    def description(self):
        return self._data.get(SCALE_DESCRIPTION, None)

    @description.setter
    def description(self, description):
        self._data[SCALE_DESCRIPTION] = description

    @property
    def data_type(self):
        return self._data.get(SCALE_DATA_TYPE, None)

    @data_type.setter
    def data_type(self, data_type):
        self._data[SCALE_DATA_TYPE] = data_type

    @property
    def decimal_places(self):
        return self._data.get(SCALE_DECIMAL_PLACES, None)

    @decimal_places.setter
    def decimal_places(self, decimal_places):
        self._data[SCALE_DECIMAL_PLACES] = decimal_places

    @property
    def min(self):
        return self._data.get(SCALE_MIN, None)

    @min.setter
    def min(self, min_):
        self._data[SCALE_MIN] = min_

    @property
    def max(self):
        return self._data.get(SCALE_MAX, None)

    @max.setter
    def max(self, max_):
        self._data[SCALE_MAX] = max_

    @property
    def valid_values(self):
        return self._data.get(SCALE_VALID_VALUES, None)

    @valid_values.setter
    def valid_values(self, valid_values):
        self._data[SCALE_VALID_VALUES] = valid_values

    def _populate_with_instance(self, instance, fields):
        accepted_fields = SCALE_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or SCALE_NAME in fields:
            self.name = instance.name
        if fields is None or SCALE_DESCRIPTION in fields:
            self.description = instance.description
        if fields is None or SCALE_DECIMAL_PLACES in fields:
            self.decimal_places = instance.decimal_places
        if fields is None or SCALE_DATA_TYPE in fields:
            self.data_type = instance.data_type.name
        if fields is None or SCALE_MIN in fields:
            self.min = instance.min
        if fields is None or SCALE_MAX in fields:
            self.max = instance.max
        if fields is None or SCALE_VALID_VALUES in fields:
            self.valid_values = instance.valid_values


def create_scale_in_db(api_data, user):
    try:
        struct = ScaleStruct(api_data)
    except ScaleValidationError as error:
        print(error)
        raise

    try:
        data_type = ScaleDataType.objects.get(name=struct.data_type)
    except ScaleDataType.DoesNotExist:
        raise ValidationError('data type not valid: ' + struct.data_type)

    group = user.groups.first()

    with transaction.atomic():
        try:
            scale = Scale.objects.create(
                name=struct.name,
                description=struct.description,
                data_type=data_type,
                decimal_places=struct.decimal_places,
                min=struct.min,
                max=struct.max,
                group=group)
        except IntegrityError:
            msg = 'This scale already exists in db: {}'.format(struct.name)
            raise ValueError(msg)
    if struct.data_type in ('Cardinal', 'Ordinal', 'Nominal'):
        for index, category in enumerate(struct.valid_values):
            ScaleCategory.objects.create(scale=scale, category=category, rank=index)

    return scale


def update_scale_in_db(api_data, instance, _):
    try:
        struct = ScaleStruct(api_data)
    except ScaleValidationError as error:
        print(error)
        raise

    try:
        data_type = ScaleDataType.objects.get(name=struct.data_type)
    except ScaleDataType.DoesNotExist:
        raise ValidationError('data type not valid: ' + struct.data_type)

    if instance.description != struct.description:
        instance.description = struct.description
    if instance.data_type != data_type:
        instance.data_type = data_type
    if instance.max != struct.max:
        instance.max = struct.max
    if instance.min != struct.min:
        instance.min = struct.min
    if instance.decimal_places != struct.decimal_places:
        instance.decimal_places = struct.decimal_places

    instance.save()
    if struct.data_type in ('Cardinal', 'Ordinal', 'Nominal'):
        ScaleCategory.objects.filter(scale=instance).delete()
        for index, category in enumerate(struct.valid_values):
            ScaleCategory.objects.create(scale=instance, category=category, rank=index)

    return instance
