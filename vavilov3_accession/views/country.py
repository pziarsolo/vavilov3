from rest_framework import viewsets

from vavilov3_accession.views.shared import (DynamicFieldsViewMixin,
                                             StandardResultsSetPagination)

from vavilov3_accession.models import Country
from vavilov3_accession.serializers.country import CountrySerializer
from vavilov3_accession.filters.country import CountryFilter


class CountryViewSet(DynamicFieldsViewMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_class = CountryFilter
    lookup_field = 'code'
    pagination_class = StandardResultsSetPagination
