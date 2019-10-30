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

from vavilov3.entities.tags import GROUP, IS_PUBLIC


class MetadataValidationError(Exception):
    pass


def validate_metadata_data(data, fields_to_validate=None):
    if fields_to_validate is None:
        fields_to_validate = (IS_PUBLIC, GROUP)
    for key in fields_to_validate:
        if key not in data:
            msg = '{} is mandatory in metadata'.format(key)
            raise MetadataValidationError(msg)


class Metadata():

    def __init__(self, data=None):
        if data:
            self._data = data
        else:
            self._data = {}

    @property
    def group(self):
        return self._data[GROUP] if GROUP in self._data else None

    @group.setter
    def group(self, group):
        self._data[GROUP] = group

    @property
    def is_public(self):
        return self._data[IS_PUBLIC] if IS_PUBLIC in self._data else None

    @is_public.setter
    def is_public(self, is_public):
        assert isinstance(is_public, bool), "is_public must be a Boolean"
        self._data[IS_PUBLIC] = is_public

    @property
    def data(self):
        return self._data
