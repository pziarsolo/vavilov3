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

from vavilov3.filters.shared import TermFilterMixin
from vavilov3.models import Study
from datetime import date
from rest_framework.exceptions import ValidationError
from vavilov3.views import format_error_message


class StudyFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    is_public = filters.BooleanFilter()
    group = filters.CharFilter(field_name='group__name', lookup_expr='exact')
    name = filters.CharFilter(field_name='name', lookup_expr='iexact')
    name_icontains = filters.CharFilter(field_name='name',
                                        lookup_expr='icontains')
    name_or_description = filters.CharFilter(method='name_or_desc')
    is_active = filters.BooleanFilter()
    contact = filters.CharFilter(label='Contact', field_name='data__contacts', lookup_expr='iexact')
    contact_contains = filters.CharFilter(label='Contact contain',
                                          field_name='data__contacts',
                                          lookup_expr='icontains')
    location = filters.CharFilter(label='Location',
                                  field_name='data__location', lookup_expr='iexact')
    location_contains = filters.CharFilter(label='Location contains',
                                           field_name='data__location',
                                           lookup_expr='icontains')
    institute = filters.CharFilter(label='institute', lookup_expr='iexact',
                                   field_name='observationunit__accession__institute__code',
                                   distinct=True)
    germplasm_number = filters.CharFilter(label='germplasm_number', lookup_expr='iexact',
                                          field_name='observationunit__accession__germplasm_number',
                                          distinct=True)
    taxon = filters.CharFilter(
        label='taxon',
        field_name='observationunit__accession__passports__taxa__name',
        lookup_expr='exact', distinct=True)

    rank = filters.CharFilter(
        label='rank',
        field_name='observationunit__accession__passports__taxa__rank__name',
        lookup_expr='exact', distinct=True)

    year = filters.CharFilter(label='Year', method='year_filter')

    class Meta:
        model = Study
        fields = {'description': ['icontains']}

    def name_or_desc(self, queryset, _, value):
        return queryset.filter(Q(name__icontains=value) |
                               Q(description__icontains=value))

    def year_filter(self, queryset, _, value):
        try:
            if len(value) != 4:
                raise ValueError('Year must be a string of 4 digits')
            year = int(value)
        except ValueError as error:
            raise ValidationError(format_error_message(error))
        year_start = date(year=year, month=1, day=1)
        year_end = date(year=year, month=12, day=31)
        return queryset.filter(Q(start_date__gte=year_start, start_date__lte=year_end) |
                               Q(end_date__gte=year_start, end_date__lte=year_end) |
                               Q(start_date__lte=year_start, end_date__gte=year_end))
