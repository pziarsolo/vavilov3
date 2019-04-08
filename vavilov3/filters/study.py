from django.db.models import Q
from django_filters import rest_framework as filters

from vavilov3.filters.shared import TermFilterMixin
from vavilov3.models import Study


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

    class Meta:
        model = Study
        fields = {'description': ['icontains']}

    def name_or_desc(self, queryset, _, value):
        return queryset.filter(Q(name__icontains=value) |
                               Q(description__icontains=value))
