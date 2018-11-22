from django_filters import rest_framework as filters

from vavilov3_accession.filters.shared import TermFilterMixin
from vavilov3_accession.models import Country
from django.db.models.aggregates import Count


class CountryFilter(TermFilterMixin, filters.FilterSet):
    code = filters.CharFilter(lookup_expr='iexact')
    name = filters.CharFilter(lookup_expr='icontains')
    term = filters.CharFilter(method='term_filter')
    only_with_accessions = filters.BooleanFilter(
        method='only_with_accessions_filter')

    class Meta:
        model = Country
        fields = ['code', 'name']

    def only_with_accessions_filter(self, queryset, _, value):
        queryset = queryset.annotate(
            num_accessionss=Count("passport__accession", distinct=True))
        if value:
            queryset = queryset.filter(num_accessionss__gt=0)
        else:
            queryset = queryset.exclude(num_accessionss__gt=0)

        queryset = queryset.order_by('-num_accessionss')

        return queryset
