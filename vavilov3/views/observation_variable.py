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

from rest_framework import viewsets, status

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin, CheckBeforeRemoveMixim)
from vavilov3.serializers.observation_variable import (
    ObservationVariableSerializer)
from vavilov3.models import ObservationVariable, Observation
from vavilov3.permissions import UserGroupObjectPermission
from vavilov3.filters.observation_variable import ObservationVariableFilter
from vavilov3.entities.observation_variable import ObservationVariableStruct
from rest_framework.response import Response
from vavilov3.views import format_error_message


class ObservationVariableViewSet(DynamicFieldsViewMixin,
                                 CheckBeforeRemoveMixim,
                                 viewsets.ModelViewSet,
                                 BulkOperationsMixin):
    lookup_field = "name"
    serializer_class = ObservationVariableSerializer
    queryset = ObservationVariable.objects.all()
    filter_class = ObservationVariableFilter
    permission_classes = (UserGroupObjectPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationVariableStruct

    def check_before_remove(self, instance):
        if Observation.objects.filter(observation_variable=instance).count():
            msg = 'Can not delete this pbservation variable because there are observations'
            msg += ' associated with it'
            return Response(format_error_message(msg),
                            status=status.HTTP_400_BAD_REQUEST)
