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

from vavilov3.views import format_error_message
from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.observation_image import (
    ObservationImageValidationError, ObservationImageStruct,
    validate_observation_image_data, create_observation_image_in_db)
from rest_framework.fields import empty


class ObservationImageMixinSerializer():
    data_type = 'observation_image'

    def validate_data(self, data):
        conf = self.context['view'].conf
        return validate_observation_image_data(data, conf=conf)

    def update_item_in_db(self, payload, instance, user):
        raise NotImplementedError('update not implemented')
        # return update_observation_image_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        conf = self.context['view'].conf
        return create_observation_image_in_db(item, user, conf=conf)


class ObservationImageListSerializer(ObservationImageMixinSerializer,
                                     VavilovListSerializer):
    pass


class ObservationImageSerializer(ObservationImageMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = ObservationImageListSerializer
        Struct = ObservationImageStruct
        ValidationError = ObservationImageValidationError

    def run_validation(self, data=empty):
        try:
            self.validate_data(data,)
        except self.Meta.ValidationError as error:
            raise ValidationError(format_error_message(error))
        return data
