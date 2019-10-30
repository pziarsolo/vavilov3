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

from django_filters.filters import DateTimeFromToRangeFilter
from vavilov3.models import ObservationImage


class ObservationImageFilter(filters.FilterSet):
    group = filters.CharFilter(field_name='observation_unit__study__group__name',
                               lookup_expr='exact')
    is_public = filters.BooleanFilter(field_name='observation_unit__study__is_public')
    study = filters.CharFilter(field_name='observation_unit__study__name',
                               lookup_expr='iexact')
    study_contains = filters.CharFilter(field_name='observation_unit__study__name',
                                        lookup_expr='icontains')

    observation_unit = filters.CharFilter(field_name='observation_unit__name',
                                          lookup_expr='iexact')
    observation_unit_contains = filters.CharFilter(field_name='observation_unit__name',
                                                   lookup_expr='icontains')
    plant = filters.CharFilter(field_name='observation_unit__plants__name',
                               lookup_expr='iexact')
    plant_contain = filters.CharFilter(field_name='observation_unit__plants__name',
                                       lookup_expr='icontains')
    accession_number = filters.CharFilter(field_name='observation_unit__accession__germplasm_number',
                                          lookup_expr='iexact')
    accession_number_contains = filters.CharFilter(field_name='observation_unit__accession__germplasm_number',
                                                   lookup_expr='icontains')
    accession_institute = filters.CharFilter(field_name='observation_unit__accession__institute__code',
                                             lookup_expr='iexact')
    accession_institute_contains = filters.CharFilter(field_name='observation_unit__accession__institute__code',
                                                      lookup_expr='icontains')
    created = DateTimeFromToRangeFilter(field_name='creation_time')

    class Meta:
        model = ObservationImage
        fields = {'observer': ['exact', 'iexact', 'icontains'],
                  'observation_image_uid': ['iexact']}
