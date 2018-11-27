from django.db.models import Q
from django_filters import rest_framework as filters

from vavilov3_accession.filters.shared import TermFilterMixin
from vavilov3_accession.models import AccessionSet


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

    is_available = filters.BooleanFilter()

    # passport realted filters
    country = filters.CharFilter(
        field_name='accessions__passports__country__code', lookup_expr='iexact',
        distinct=True)
    biological_status = filters.CharFilter(
        field_name='accessions__passports__biological_status', lookup_expr='exact',
        distinct=True)
    collection_source = filters.CharFilter(
        field_name='accessions__passports__collection_source', lookup_expr='exact',
        distinct=True)
    taxon = filters.CharFilter(
        label='Passport taxon',
        field_name='accessions__passports__taxonpassport__taxon__name',
        lookup_expr='iexact', distinct=True)
    taxon_contains = filters.CharFilter(
        label='Passport taxon contains',
        field_name='accessions__passports__taxonpassport__taxon__name',
        lookup_expr='icontains', distinct=True)
    rank = filters.CharFilter(
        label='Passport rank',
        field_name='accessions__passports__taxonpassport__taxon__rank__name',
        lookup_expr='exact', distinct=True)

    class Meta:
        model = AccessionSet
        fields = {'accessionset_number': ['icontains']}