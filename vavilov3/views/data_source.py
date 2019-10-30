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
                                   StandardResultsSetPagination)
from vavilov3.models import DataSource
from vavilov3.serializers.data_source import DataSourceSerializer
from vavilov3.filters.data_source import DataSourceFilter


class DataSourceViewSet(DynamicFieldsViewMixin, viewsets.ReadOnlyModelViewSet):
    lookup_field = 'code'
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    filterset_class = DataSourceFilter
    pagination_class = StandardResultsSetPagination
