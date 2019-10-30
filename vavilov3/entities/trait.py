#
# Copyright (C) 2019 P.Ziarsolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from copy import deepcopy

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.exceptions import ValidationError

from vavilov3.entities.tags import (TRAIT_NAME, TRAIT_DESCRIPTION, ONTOLOGY_ID,
                                    ONTOLOGY_NAME)

from vavilov3.views import format_error_message
from vavilov3.models import Trait
from vavilov3.id_validator import validate_name

TRAIT_ALLOWED_FIELDS = (TRAIT_NAME, TRAIT_DESCRIPTION, ONTOLOGY_NAME, ONTOLOGY_ID)


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
    try:
        validate_name(data[TRAIT_NAME])
    except ValueError as msg:
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

    @property
    def ontology(self):
        return self._data.get(ONTOLOGY_NAME, None)

    @ontology.setter
    def ontology(self, ontology):
        self._data[ONTOLOGY_NAME] = ontology

    @property
    def ontology_id(self):
        return self._data.get(ONTOLOGY_ID, None)

    @ontology_id.setter
    def ontology_id(self, ontology_id):
        self._data[ONTOLOGY_ID] = ontology_id

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
        if fields is None or ONTOLOGY_NAME in fields:
            self.ontology = instance.ontology
        if fields is None or ONTOLOGY_ID in fields:
            self.ontology_id = instance.ontology_id


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
                description=struct.description,
                ontology=struct.ontology,
                ontology_id=struct.ontology_id)
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
    if instance.ontology != struct.ontology:
        instance.ontology = struct.ontology
    if instance.ontology_id != struct.ontology_id:
        instance.ontology_id = struct.ontology_id
    instance.save()

    return instance


def parse_obo(fhand):
    in_term = False
    term = None
    terms = []
    for line in fhand:
        line = line.strip()
        if not line:
            continue

        if line.startswith('[Term]'):
            in_term = True
            if term is not None and 'name' in term:
                terms.append(term)
                term = None
            elif term is not None and 'name' in term:
                term = None
        elif line.startswith('[Typedef]'):
            in_term = False
        elif line.startswith('ontology:'):
            ontology = line.split(':', 1)[1].strip()
        elif in_term:
            if term is None:
                term = {}

            key, value = line.split(':', 1)
            term[key.strip()] = value.strip()
    return {'name': ontology, 'terms': terms}


def transform_to_trait_entity_format(ontology):
    ont_name = ontology['name']
    traits = []
    for term in ontology['terms']:
        obsolete = term.get('is_obsolete', False)
        if obsolete == 'true':
            obsolete = True
        name = term['name']
        description = term.get('def', None)
        if not description:
            description = name
        else:
            description = description.replace('"', '')
        if obsolete:
            name += ' OBSOLETE'

        if name == 'grain length to width ratio' and term['id'] == 'TO:0000411':
            name = name + ' 2'
        trait = {'name': name,
                 'description': description,
                 'ontology': ont_name,
                 'ontology_id': term['id']}
        traits.append(trait)
    return traits
