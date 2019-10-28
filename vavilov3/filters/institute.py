from django.db.models import Q
from django_filters import rest_framework as filters
from django.db.models.aggregates import Count

from vavilov3.models import Institute
from vavilov3.filters.shared import TermFilterMixin
from vavilov3.conf import settings


class InstituteFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    code_or_name = filters.CharFilter(label='code_or_name',
                                      method='code_or_name_filter')
    only_with_accessions = filters.CharFilter(label='only_with_accessions',
                                              method='only_with_accession_filter')

    class Meta:
        model = Institute
        fields = {'code': ['exact', 'iexact', 'icontains'],
                  'name': ['exact', 'iexact', 'icontains']}

    def code_or_name_filter(self, queryset, _, value):
        return queryset.filter(Q(name__icontains=value) |
                               Q(code__icontains=value))

    def only_with_accession_filter(self, queryset, _, value):
        queryset = queryset.annotate(num_accessionss=Count("accession",
                                                           distinct=True))
        if value in settings.VALID_TRUE_VALUES:
            queryset = queryset.filter(num_accessionss__gt=0)
        else:
            queryset = queryset.exclude(num_accessionss__gt=0)

        queryset = queryset.order_by('-num_accessionss')
        return queryset
