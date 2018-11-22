from rest_framework import viewsets
from vavilov3_accession.views.shared import (DynamicFieldsViewMixin,
                                             StandardResultsSetPagination)
from vavilov3_accession.models import DataSource
from vavilov3_accession.serializers.data_source import DataSourceSerializer
from vavilov3_accession.filters.data_source import DataSourceFilter


class DataSourceViewSet(DynamicFieldsViewMixin, viewsets.ReadOnlyModelViewSet):
    lookup_field = 'code'
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    filterset_class = DataSourceFilter
    pagination_class = StandardResultsSetPagination
