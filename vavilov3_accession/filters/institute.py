from django.db.models import Q
from django_filters import rest_framework as filters

from vavilov3_accession.models import Institute
from vavilov3_accession.filters.shared import TermFilterMixin


class InstituteFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    code_or_name = filters.CharFilter(label='code_or_name',
                                      method='code_or_name_filter')
    #  only_with_passports = filters.BooleanFilter(label='only_with_items',
    #    method='only_with_passports_filter')

    class Meta:
        model = Institute
        fields = {'code': ['exact', 'iexact', 'icontains'],
                  'name': ['exact', 'iexact', 'icontains']}

    def code_or_name_filter(self, queryset, _, value):
        return queryset.filter(Q(name__icontains=value) |
                               Q(code__icontains=value))
#     def only_with_passports_filter(self, queryset, _, value):
#         queryset = queryset.annotate(num_passports=Count(
#             "passport_institute",distinct=True))
#         queryset = queryset.filter(num_passports__gt=0)
#         queryset = queryset.order_by('-num_passports')
#         return queryset
