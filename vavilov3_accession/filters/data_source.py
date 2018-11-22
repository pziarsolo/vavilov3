from django_filters import rest_framework as filters

from vavilov3_accession.filters.shared import TermFilterMixin
from vavilov3_accession.models import DataSource


class DataSourceFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(field_name='code', lookup_expr='icontains')
    code = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = DataSource
        fields = ('code', 'kind')
