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

from vavilov3.models import ObservationUnit
from vavilov3.filters.shared import TermFilterMixin


class ObservationUnitFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    study = filters.CharFilter(field_name='study__name', lookup_expr='iexact')
    study_contains = filters.CharFilter(field_name='study__name',
                                        lookup_expr='icontains')
    group = filters.CharFilter(field_name='study__group__name', lookup_expr='exact')
    accession = filters.CharFilter(field_name='accession__germplasm_number',
                                   lookup_expr='iexact')
    accession_contains = filters.CharFilter(field_name='accession__germplasm_number',
                                            lookup_expr='contains')
    plant = filters.CharFilter(label='Plant', field_name='plant__name',
                               lookup_expr='iexact')
    plant_contains = filters.CharFilter(label='Plant', field_name='plant__name',
                                        lookup_expr='icontains', distinct=True)

    plant_number = filters.CharFilter(label='Plant number', field_name='plant__plant_number',
                                      lookup_expr='iexact')
    entry_number = filters.CharFilter(label='Plant entry ',
                                      field_name='plant__entry_number',
                                      lookup_expr='iexact')
    block_number = filters.CharFilter(label='Plant Block ',
                                      field_name='plant__block_number',
                                      lookup_expr='iexact')
    plot_number = filters.CharFilter(label='Plant Plot ',
                                     field_name='plant__plot_number',
                                     lookup_expr='iexact')

    class Meta:
        model = ObservationUnit
        fields = {'name': ['exact', 'iexact', 'icontains'],
                  'level': ['exact', 'iexact', 'icontains'],
                  'replicate': ['exact', 'iexact']}

    def plant_filter(self, queryset, _, value):
        return queryset.filter(
            Q(plant__name__icontains=value) |
            Q(plant__block_number__icontains=value) |
            Q(plant__entry_number__icontains=value) |
            Q(plant__plant_number__icontains=value) |
            Q(plant__plot_number__icontains=value)).distinct()
