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
#

from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from vavilov3.views import format_error_message
from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer

from vavilov3.entities.trait import (TraitStruct, TraitValidationError,
                                     create_trait_in_db, update_trait_in_db,
                                     validate_trait_data)


class TraitMixinSerializer():
    data_type = 'trait'

    def validate_data(self, data):
        return validate_trait_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_trait_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_trait_in_db(item, user)


class TraitListSerializer(TraitMixinSerializer, VavilovListSerializer):
    pass


class TraitSerializer(TraitMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = TraitListSerializer
        Struct = TraitStruct
        ValidationError = TraitValidationError

    def run_validation(self, data=empty):
        try:
            self.validate_data(data)
        except self.Meta.ValidationError as error:
            raise ValidationError(format_error_message(error))
        return data
