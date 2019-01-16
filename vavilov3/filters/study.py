from django_filters import rest_framework as filters

from vavilov3.filters.shared import TermFilterMixin
from vavilov3.models import Study


class StudyFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    is_public = filters.BooleanFilter()
    group = filters.CharFilter(field_name='group__name', lookup_expr='exact')
    name = filters.CharFilter(field_name='name', lookup_expr='iexact')
    name_contains = filters.CharFilter(field_name='name',
                                       lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    contact = filters.CharFilter(field_name='contacts', lookup_expr='iexact')
    location = filters.CharFilter(field_name='location', lookup_expr='iexact')
    location_contains = filters.CharFilter(field_name='location',
                                           lookup_expr='icontains')

    class Meta:
        model = Study
        fields = {'description': ['icontains']}
