from django.db.models import Q
from django_filters import rest_framework as filters

from vavilov3_accession.filters.shared import TermFilterMixin
from vavilov3_accession.models import Accession


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
        field_name='passports__taxonpassport__taxon__name',
        lookup_expr='iexact', distinct=True)
    taxon_contains = filters.CharFilter(
        field_name='passports__taxonpassport__taxon__name',
        lookup_expr='icontains', distinct=True)
    rank = filters.CharFilter(
        field_name='passports__taxonpassport__taxon__rank__name',
        lookup_expr='exact', distinct=True)

    numbers = filters.CharFilter(method='number_filter', distinct=True)

    class Meta:
        model = Accession
        fields = {'germplasm_number': ['icontains']}

    def number_filter(self, queryset, _, value):
        queryset = queryset.filter(
            Q(germplasm_number__icontains=value) |
            Q(passports__accession_name__icontains=value) |
            Q(passports__collection_number__icontains=value)).distinct()
        return queryset
