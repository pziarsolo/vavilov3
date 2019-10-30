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

from vavilov3.serializers.shared import VavilovSerializer, VavilovListSerializer
from vavilov3.entities.accessionset import (AccessionSetStruct,
                                            AccessionSetValidationError,
                                            validate_accessionset_data,
                                            create_accessionset_in_db,
                                            update_accessionset_in_db)


class AccessionSetMixinSerializer():
    data_type = 'accessionset'

    def create_item_in_db(self, item, user):
        return create_accessionset_in_db(item, user)

    def update_item_in_db(self, payload, instance, user):
        return update_accessionset_in_db(payload, instance, user)

    def validate_data(self, data):
        return validate_accessionset_data(data)


class AccessionSetListSerializer(AccessionSetMixinSerializer, VavilovListSerializer):
    pass


class AccessionSetSerializer(AccessionSetMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = AccessionSetListSerializer
        Struct = AccessionSetStruct
        ValidationError = AccessionSetValidationError
