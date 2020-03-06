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
from vavilov3.models import Accession


class AccessionFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    is_public = filters.BooleanFilter()
    group = filters.CharFilter(field_name='group__name', lookup_expr='exact')
    institute_code = filters.CharFilter(field_name='institute__code',
                                        lookup_expr='iexact')
    institute_code_icontains = filters.CharFilter(field_name='institute__code',
                                                  lookup_expr='icontains')
    germplasm_number = filters.CharFilter(field_name='germplasm_number',
                                          lookup_expr='iexact')

    is_available = filters.BooleanFilter()
    in_nulear_collection = filters.BooleanFilter()

    # passport realted filters
    country = filters.CharFilter(
        field_name='passports__country__code', lookup_expr='iexact',
        distinct=True)
    biological_status = filters.CharFilter(
        field_name='passports__biological_status', lookup_expr='exact',
        distinct=True)
    collection_source = filters.CharFilter(
        field_name='passports__collection_source', lookup_expr='exact',
        distinct=True)
    taxon = filters.CharFilter(
        label='Passport taxon',
        field_name='passports__taxa__name',
        lookup_expr='iexact', distinct=True)
    taxon_contains = filters.CharFilter(
        label='Passport taxon contains',
        field_name='passports__taxa__name',
        lookup_expr='icontains', distinct=True)
    rank = filters.CharFilter(
        label='Passport rank',
        field_name='passports__taxa__rank__name',
        lookup_expr='exact', distinct=True)

    number_contains = filters.CharFilter(
        label='Any accession number in entity',
        method='number_filter', distinct=True)
    site = filters.CharFilter(label='site', method='site_filter')

    study = filters.CharFilter(label='study', field_name='observationunit__study__name',
                               lookup_expr='iexact', distinct=True)
    study_icontains = filters.CharFilter(label='study', field_name='observationunit__study__name',
                                         lookup_expr='icontains', distinct=True)

    class Meta:
        model = Accession
        fields = {'germplasm_number': ['icontains']}

    def number_filter(self, queryset, _, value):
        queryset = queryset.filter(
            Q(germplasm_number__icontains=value) |
            Q(passports__accession_name__icontains=value) |
            Q(passports__collection_number__icontains=value)).distinct()
        return queryset

    def site_filter(self, queryset, _, value):
        return queryset.filter(
            Q(passports__state__icontains=value) |
            Q(passports__province__icontains=value) |
            Q(passports__municipality__icontains=value) |
            Q(passports__location_site__icontains=value)).distinct()
