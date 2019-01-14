from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)

from vavilov3.models import Country
from vavilov3.serializers.country import CountrySerializer
from vavilov3.filters.country import CountryFilter


class CountryViewSet(DynamicFieldsViewMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_class = CountryFilter
    lookup_field = 'code'
    pagination_class = StandardResultsSetPagination
