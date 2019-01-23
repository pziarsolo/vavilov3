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
