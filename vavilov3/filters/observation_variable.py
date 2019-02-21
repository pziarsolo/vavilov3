from django_filters import rest_framework as filters

from vavilov3.models import ObservationVariable
from vavilov3.filters.shared import TermFilterMixin


class ObservationVariableFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    group = filters.CharFilter(field_name='group__name', lookup_expr='exact')

    class Meta:
        model = ObservationVariable
        fields = {'name': ['exact', 'iexact', 'icontains'],
                  'description': ['exact', 'iexact', 'icontains'],
                  'trait__name': ['exact', 'iexact', 'icontains'],
                  'method': ['exact', 'iexact', 'icontains'],
                  'scale__name': ['exact', 'iexact', 'icontains'], }
