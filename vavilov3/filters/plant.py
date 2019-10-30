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

from django_filters import rest_framework as filters

from vavilov3.models import Plant
from vavilov3.filters.shared import TermFilterMixin


class PlantFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    group = filters.CharFilter(field_name='group__name', lookup_expr='exact')
    observation_unit = filters.CharFilter(field_name='observation_units__name',
                                          lookup_expr='iexact',
                                          distinct=True)
    observation_unit_contains = filters.CharFilter(field_name='observation_units__name',
                                                   lookup_expr='icontains',
                                                   distinct=True)
    study = filters.CharFilter(field_name='observation_units__study__name',
                               lookup_expr='iexact',
                               distinct=True)
    study_contains = filters.CharFilter(field_name='observation_units__study__name',
                                        lookup_expr='icontains',
                                        distinct=True)

    class Meta:
        model = Plant
        fields = {'name': ['exact', 'iexact', 'icontains'],
                  'x': ['exact', 'iexact', 'icontains'],
                  'y': ['exact', 'iexact', 'icontains'],
                  'block_number': ['exact', 'iexact', 'icontains'],
                  'entry_number': ['exact', 'iexact', 'icontains'],
                  'plant_number': ['exact', 'iexact', 'icontains'],
                  'plot_number': ['exact', 'iexact', 'icontains']}
