from django.db.models import Q
from django_filters import rest_framework as filters

from vavilov3.filters.shared import TermFilterMixin
from vavilov3.models import AccessionSet


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

    class Meta:
        model = AccessionSet
        fields = {'accessionset_number': ['icontains']}

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
