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
from vavilov3.entities.plant import (PlantStruct, PlantValidationError,
                                     validate_plant_data, update_plant_in_db,
                                     create_plant_in_db)
from vavilov3.entities.tags import GROUP


class PlantMixinSerializer():
    data_type = 'plant'

    def validate_data(self, data):
        return validate_plant_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_plant_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_plant_in_db(item, user)


class PlantListSerializer(PlantMixinSerializer, VavilovListSerializer):
    pass


class PlantSerializer(PlantMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = PlantListSerializer
        Struct = PlantStruct
        ValidationError = PlantValidationError
        metadata_validation_fields = [GROUP]
