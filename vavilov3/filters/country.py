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
from django.db.models.aggregates import Count

from vavilov3.filters.shared import TermFilterMixin
from vavilov3.models import Country
from vavilov3.conf import settings


class CountryFilter(TermFilterMixin, filters.FilterSet):
    code = filters.CharFilter(lookup_expr='iexact')
    name = filters.CharFilter(lookup_expr='icontains')
    term = filters.CharFilter(method='term_filter',
                              label='Term')
    code_or_name = filters.CharFilter(label='code_or_name',
                                      method='code_or_name_filter')
    only_with_accessions = filters.BooleanFilter(
        label='only_with_accessions',
        method='only_with_accessions_filter')

    class Meta:
        model = Country
        fields = ['code', 'name']

    def code_or_name_filter(self, queryset, _, value):
        return queryset.filter(Q(name__icontains=value) |
                               Q(code__icontains=value))

    def only_with_accessions_filter(self, queryset, _, value):
        queryset = queryset.annotate(
            num_accessionss=Count("passport__accession", distinct=True))
        if value in settings.VALID_TRUE_VALUES:
            queryset = queryset.filter(num_accessionss__gt=0)
        else:
            queryset = queryset.exclude(num_accessionss__gt=0)

        queryset = queryset.order_by('-num_accessionss')

        return queryset
