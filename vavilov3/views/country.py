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

from django.db.models.aggregates import Count

from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)

from vavilov3.models import Country
from vavilov3.serializers.country import CountrySerializer
from vavilov3.filters.country import CountryFilter


class CountryViewSet(DynamicFieldsViewMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_class = CountryFilter
    lookup_field = 'code'
    pagination_class = StandardResultsSetPagination
    ordering_fields = ('code', 'name', 'by_num_accessions', 'by_num_accessionsets')
    ordering = ('-by_num_accessions',)

    def get_queryset(self):
        return self.queryset.annotate(by_num_accessions=Count('passport__accession', distinc=True),
                                      by_num_accessionsets=Count('passport__accession__accessionset', distint=True))
