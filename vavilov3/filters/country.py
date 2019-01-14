from django.db.models import Q
from django_filters import rest_framework as filters
from django.db.models.aggregates import Count

from vavilov3.filters.shared import TermFilterMixin
from vavilov3.models import Country


class CountryFilter(TermFilterMixin, filters.FilterSet):
    code = filters.CharFilter(lookup_expr='iexact')
    name = filters.CharFilter(lookup_expr='icontains')
    term = filters.CharFilter(method='term_filter',
                              label='Term')
    code_or_name = filters.CharFilter(label='code_or_name',
                                      method='code_or_name_filter')
    only_with_accessions = filters.BooleanFilter(
        label='only_with_accessions',
        method='only_with_accessions_filter')

    class Meta:
        model = Country
        fields = ['code', 'name']

    def code_or_name_filter(self, queryset, _, value):
        return queryset.filter(Q(name__icontains=value) |
                               Q(code__icontains=value))

    def only_with_accessions_filter(self, queryset, _, value):
        queryset = queryset.annotate(
            num_accessionss=Count("passport__accession", distinct=True))
        if value:
            queryset = queryset.filter(num_accessionss__gt=0)
        else:
            queryset = queryset.exclude(num_accessionss__gt=0)

        queryset = queryset.order_by('-num_accessionss')

        return queryset
