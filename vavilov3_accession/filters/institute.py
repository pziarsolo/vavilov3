from django.db.models import Q

from django_filters import rest_framework as filters
from vavilov3_accession.models import Institute


class TermFilterMixin():

    def term_filter(self, qs, _, value):
        return qs.filter(Q(code__icontains=value) |
                         Q(name__icontains=value))


class InstituteFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
#     only_with_passports = filters.BooleanFilter(label='only_with_items', method='only_with_passports_filter')

    class Meta:
        model = Institute
        fields = {'code': ['exact', 'iexact', 'icontains'],
                  'code': ['exact', 'iexact', 'icontains']}

#     def only_with_passports_filter(self, queryset, _, value):
#         queryset = queryset.annotate(num_passports=Count("passport_institute", distinct=True))
#         queryset = queryset.filter(num_passports__gt=0)
#         queryset = queryset.order_by('-num_passports')
#         return queryset
