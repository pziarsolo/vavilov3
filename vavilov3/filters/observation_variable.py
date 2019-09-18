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
