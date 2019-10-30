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

from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   ByObjectStudyPermMixin, BulkOperationsMixin,
                                   CheckBeforeRemoveMixim)
from vavilov3.models import ObservationUnit
from vavilov3.permissions import ObservationUnitByStudyPermission
from vavilov3.serializers.observation_unit import ObservationUnitSerializer
from vavilov3.entities.observation_unit import ObservationUnitStruct
from vavilov3.filters.observation_unit import ObservationUnitFilter


class ObservationUnitViewSet(ByObjectStudyPermMixin, DynamicFieldsViewMixin,
                             CheckBeforeRemoveMixim,
                             viewsets.ModelViewSet, BulkOperationsMixin):
    lookup_field = "name"
    serializer_class = ObservationUnitSerializer
    queryset = ObservationUnit.objects.all()
    filter_class = ObservationUnitFilter
    permission_classes = (ObservationUnitByStudyPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationUnitStruct
