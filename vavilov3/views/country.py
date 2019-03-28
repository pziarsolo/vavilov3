from django.db.models.aggregates import Count

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
    ordering_fields = ('code', 'name', 'by_num_accessions', 'by_num_accessionsets')
    ordering = ('-by_num_accessions',)

    def get_queryset(self):
        return self.queryset.annotate(by_num_accessions=Count('passport__accession', distinc=True),
                                      by_num_accessionsets=Count('passport__accession__accessionset', distint=True))
