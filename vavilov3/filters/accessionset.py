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
from vavilov3.models import AccessionSet
from vavilov3.entities.tags import IS_ACTIVE
from vavilov3.conf import settings


class AccessionSetFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    is_public = filters.BooleanFilter()
    group = filters.CharFilter(field_name='group__name', lookup_expr='exact')
    institute_code = filters.CharFilter(field_name='institute__code',
                                        lookup_expr='iexact')
    institute_code_icontains = filters.CharFilter(field_name='institute__code',
                                                  lookup_expr='icontains')
    accessionset_number = filters.CharFilter(field_name='accessionset_number',
                                             lookup_expr='iexact')
    accession_institute = filters.CharFilter(field_name='accessions__institute__code',
                                             lookup_expr='iexact', distinct=True)
    accession_number = filters.CharFilter(field_name='accessions__germplasm_number',
                                          lookup_expr='iexact', distinct=True)
    is_available = filters.BooleanFilter()

    # passport realted filters
    country = filters.CharFilter(
        field_name='accessions__passports__country__code', lookup_expr='iexact',
        distinct=True)
    site = filters.CharFilter(label='site', method='site_filter')
    biological_status = filters.CharFilter(
        field_name='accessions__passports__biological_status', lookup_expr='exact',
        distinct=True)
    collection_source = filters.CharFilter(
        field_name='accessions__passports__collection_source', lookup_expr='exact',
        distinct=True)
    taxon = filters.CharFilter(
        label='Passport taxon',
        field_name='accessions__passports__taxa__name',
        lookup_expr='iexact', distinct=True)

    taxon_contains = filters.CharFilter(
        label='Passport taxon contains',
        field_name='accessions__passports__taxa__name',
        lookup_expr='icontains', distinct=True)
    rank = filters.CharFilter(
        label='Passport rank',
        field_name='accessions__passports__taxa__rank__name',
        lookup_expr='exact', distinct=True)
    number_contains = filters.CharFilter(label='Number Contain',
                                         method='number_contain_filter')

    is_available = filters.BooleanFilter(field_name='accessions__is_available')
    in_nuclear_collection = filters.BooleanFilter(field_name='accessions__in_nuclear_collection')
    seed_available = filters.BooleanFilter('Seed available',
                                           method='seed_available_filter',
                                           distinct=True)

    class Meta:
        model = AccessionSet
        fields = {'accessionset_number': ['icontains']}

    def seed_available_filter(self, queryset, _, value):
        query = (Q(accessions__is_available=True) &
                 Q(accessions__conservation_status__iexact=IS_ACTIVE))
        if value in settings.VALID_TRUE_VALUES:
            queryset = queryset.filter(query).distinct()
        return queryset

    def site_filter(self, queryset, _, value):
        queryset = queryset.filter(
            Q(accessions__passports__state__icontains=value) |
            Q(accessions__passports__province__icontains=value) |
            Q(accessions__passports__municipality__icontains=value) |
            Q(accessions__passports__location_site__icontains=value))
        return queryset.distinct()

    def number_contain_filter(self, queryset, _, value):
        queryset = queryset.filter(
            Q(accessionset_number__icontains=value) |
            Q(accessions__germplasm_number__icontains=value) |
            Q(accessions__passports__collection_number__icontains=value))
        return queryset.distinct()
