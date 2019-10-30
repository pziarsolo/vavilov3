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
from vavilov3.models import Scale, Observation
from vavilov3.permissions import IsAdminOrReadOnly

from vavilov3.serializers.scale import ScaleSerializer
from vavilov3.entities.scale import ScaleStruct
from vavilov3.filters.scale import ScaleFilter
from rest_framework.response import Response
from vavilov3.views import format_error_message


class ScaleViewSet(DynamicFieldsViewMixin, CheckBeforeRemoveMixim,
                   viewsets.ModelViewSet, BulkOperationsMixin):
    lookup_field = 'name'
    serializer_class = ScaleSerializer
    queryset = Scale.objects.all()
    filter_class = ScaleFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    Struct = ScaleStruct

    def check_before_remove(self, instance):
        if Observation.objects.filter(observation_variable__scale=instance).count():
            msg = 'Can not delete this scale because there are observations'
            msg += ' associated with it'
            return Response(format_error_message(msg),
                            status=status.HTTP_400_BAD_REQUEST)
