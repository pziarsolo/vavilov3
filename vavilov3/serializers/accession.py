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

from vavilov3.entities.accession import (AccessionValidationError,
                                         AccessionStruct,
                                         validate_accession_data,
                                         update_accession_in_db,
                                         create_accession_in_db)

from vavilov3.serializers.shared import VavilovListSerializer, VavilovSerializer
from vavilov3.entities.passport import PassportValidationError
from vavilov3.passport.validation import PassportValidationError as PassportValidationError2


class AccessionMixinSerializer():
    data_type = 'accession'

    def update_item_in_db(self, payload, instance, user):
        return update_accession_in_db(payload, instance, user)

    def create_item_in_db(self, item, user):
        return create_accession_in_db(item, user)

    def validate_data(self, data):
        try:
            return validate_accession_data(data)
        except (PassportValidationError, PassportValidationError2) as error:
            raise AccessionValidationError(error)


class AccessionListSerializer(AccessionMixinSerializer, VavilovListSerializer):
    pass


class AccessionSerializer(AccessionMixinSerializer, VavilovSerializer):

    class Meta:
        list_serializer_class = AccessionListSerializer
        Struct = AccessionStruct
        ValidationError = AccessionValidationError
