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

from django.db.models import Q
from django_filters import rest_framework as filters

from vavilov3.models import ObservationVariable
from vavilov3.filters.shared import TermFilterMixin


class ObservationVariableFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter',
                              distinct=True)
    group = filters.CharFilter(field_name='group__name', lookup_expr='exact',
                               distinct=True)
    study = filters.CharFilter(field_name='observation__observation_unit__study__name',
                               lookup_expr='iexact', distinct=True)
    name_or_desc = filters.CharFilter(label='term', method='name_or_desc_filter',
                                      distinct=True)

    class Meta:
        model = ObservationVariable
        fields = {'name': ['exact', 'iexact', 'icontains'],
                  'description': ['exact', 'iexact', 'icontains'],
                  'trait__name': ['exact', 'iexact', 'icontains'],
                  'method': ['exact', 'iexact', 'icontains'],
                  'scale__name': ['exact', 'iexact', 'icontains'], }

    def name_or_desc_filter(self, queryset, _, value):
        return queryset.filter(Q(name__icontains=value) |
                               Q(description__icontains=value))
