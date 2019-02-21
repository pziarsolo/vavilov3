
from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)
from vavilov3.models import Scale
from vavilov3.permissions import IsAdminOrReadOnly

from vavilov3.serializers.scale import ScaleSerializer
from vavilov3.entities.scale import ScaleStruct
from vavilov3.filters.scale import ScaleFilter


class ScaleViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_field = 'name'
    serializer_class = ScaleSerializer
    queryset = Scale.objects.all()
    filter_class = ScaleFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    Struct = ScaleStruct
