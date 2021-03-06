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

from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.seed_request import (validate_seed_request_data,
                                            SeedRequestStruct,
                                            SeedRequestValidationError,
                                            create_seed_request_in_db)
from vavilov3.views import format_error_message
from rest_framework.exceptions import ValidationError


class SeedRequestMixinSerializer():
    data_type = 'seed_request'

    def validate_data(self, data):
        return validate_seed_request_data(data)

    def create_item_in_db(self, item, user):
        return create_seed_request_in_db(item, user)


class SeedRequestListSerializer(SeedRequestMixinSerializer, VavilovListSerializer):
    pass


class SeedRequestSerializer(SeedRequestMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = SeedRequestListSerializer
        Struct = SeedRequestStruct
        ValidationError = SeedRequestValidationError

    def to_representation(self, instance):

        if isinstance(instance, list):
            representation = []
            for item_instance in instance:
                struct = self.Meta.Struct(instance=item_instance,
                                          fields=self.selected_fields)
                representation.append(struct.get_api_document())
            return representation
        else:
            struct = self.Meta.Struct(instance=instance,
                                      fields=self.selected_fields)

            return struct.get_api_document()

    @property
    def data(self):
        return self.to_representation(self.instance)

    def create(self, validated_data):
        try:
            return self.create_item_in_db(validated_data, None)
        except ValueError as error:
            raise ValidationError(format_error_message(error))
