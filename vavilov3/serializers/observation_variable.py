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

from vavilov3.entities.observation_variable import (
    ObservationVariableStruct, validate_observation_variable_data,
    ObservationVariableValidationError, update_observation_variable_in_db,
    create_observation_variable_in_db)
from vavilov3.entities.tags import GROUP
from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer


class ObservationVariableMixinSerializer():
    data_type = 'observation_variable'

    def validate_data(self, data):
        return validate_observation_variable_data(data)

    def update_item_in_db(self, payload, instance, user):
        return update_observation_variable_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_observation_variable_in_db(item, user)


class ObservationVariableListSerializer(ObservationVariableMixinSerializer,
                                        VavilovListSerializer):
    pass


class ObservationVariableSerializer(ObservationVariableMixinSerializer,
                                    VavilovSerializer):

    class Meta:
        list_serializer_class = ObservationVariableListSerializer
        Struct = ObservationVariableStruct
        ValidationError = ObservationVariableValidationError
        metadata_validation_fields = [GROUP]
