from rest_framework import viewsets
from vavilov3_accession.models import Institute
from vavilov3_accession.views.shared import (DynamicFieldsViewMixin,
                                             StandardResultsSetPagination)
from vavilov3_accession.serializers.institute import InstituteSerializer
from vavilov3_accession.filters.institute import InstituteFilter


class InstituteViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_field = 'code'
    queryset = Institute.objects.order_by('code')
    serializer_class = InstituteSerializer
    filter_class = InstituteFilter
#     permission_classes = (IsAdminOrReadOnly,)

    pagination_class = StandardResultsSetPagination
