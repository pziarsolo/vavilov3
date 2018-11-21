from rest_framework import viewsets
from vavilov3.models import Institute
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)
from vavilov3.serializers.institute import InstituteSerializer
from vavilov3.filters.institute import InstituteFilter


class InstituteViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_field = 'code'
    queryset = Institute.objects.order_by('code')
    serializer_class = InstituteSerializer
    filter_class = InstituteFilter
#     permission_classes = (IsAdminOrReadOnly,)

    pagination_class = StandardResultsSetPagination
