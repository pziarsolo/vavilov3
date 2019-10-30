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

from operator import and_
from functools import reduce

from django.db.models import Q

from rest_framework.filters import BaseFilterBackend
from vavilov3.models import ObservationVariable


class AccessionByObservationFilterBackend(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, _):
        observation_variables_to_filter = []
        new_query_params = {}
        for key, value in request.query_params.items():
            trait_method = key.split('__')[0]
            try:
                variable = ObservationVariable.objects.get(name=trait_method)
                observation_variables_to_filter.append((key, value, variable))
            except ObservationVariable.DoesNotExist:
                new_query_params[key] = value

        request._request.GET = new_query_params

        for filter_expresion, value, variable in observation_variables_to_filter:
            trait_filter = []
            items = filter_expresion.split('__')
            observation_variable_name = items[0]
            trait_filter.append(Q(('observationunit__observation__observation_variable__name', observation_variable_name)))
            if len(items) == 1:
                lookup_expression = 'int__exact'
            elif len(items) == 2:
                lookup_expression = 'int__{}'.format(items[1])
            trait_filter.append(Q(('observationunit__observation__value__{}'.format(lookup_expression),
                                value)))
            queryset = queryset.filter(reduce(and_, trait_filter))

        # print(queryset.query)
        return queryset
