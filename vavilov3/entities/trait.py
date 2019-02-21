from copy import deepcopy

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.entities.tags import TRAIT_NAME, TRAIT_DESCRIPTION

from vavilov3.views import format_error_message
from vavilov3.models import Trait

TRAIT_ALLOWED_FIELDS = (TRAIT_NAME, TRAIT_DESCRIPTION)


class TraitValidationError(Exception):
    pass


MANDATORY_FIELDS = [TRAIT_NAME, TRAIT_DESCRIPTION]


def validate_trait_data(data):
    for mandatory_field in MANDATORY_FIELDS:
        if mandatory_field not in data:
            raise TraitValidationError('{} mandatory'.format(mandatory_field))
    return data
    not_allowed_fields = set(data.keys()).difference(TRAIT_ALLOWED_FIELDS)

    if not_allowed_fields:
        msg = 'Not allowes fields: {}'.format(', '.join(not_allowed_fields))
        raise TraitValidationError(msg)


class TraitStruct():

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if api_data is None and instance is None:
            self._data = {}

        elif api_data:
            payload = deepcopy(api_data)
            validate_trait_data(payload)
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
        return self._data[TRAIT_NAME]

    @name.setter
    def name(self, name):
        self._data[TRAIT_NAME] = name

    @property
    def description(self):
        return self._data.get(TRAIT_DESCRIPTION, None)

    @description.setter
    def description(self, description):
        self._data[TRAIT_DESCRIPTION] = description

    def _populate_with_instance(self, instance, fields):
        accepted_fields = TRAIT_ALLOWED_FIELDS
        if (fields is not None and
                len(set(fields).intersection(accepted_fields)) == 0):
            msg = format_error_message('Passed fields are not allowed')
            raise ValidationError(msg)

        if fields is None or TRAIT_NAME in fields:
            self.name = instance.name
        if fields is None or TRAIT_DESCRIPTION in fields:
            self.description = instance.description


def create_trait_in_db(api_data, _):
    try:
        struct = TraitStruct(api_data)
    except TraitValidationError as error:
        print(error)
        raise

#     group = user.groups.first()

    with transaction.atomic():
        try:
            trait = Trait.objects.create(
                name=struct.name,
                description=struct.description)
        except IntegrityError:
            msg = 'This trait already exists in db: {}'.format(struct.name)
            raise ValueError(msg)

    return trait


def update_trait_in_db(api_data, instance, _):
    try:
        struct = TraitStruct(api_data)
    except TraitValidationError as error:
        print(error)
        raise

    if instance.description != struct.description:
        instance.description = struct.description
        instance.save()

    return instance
