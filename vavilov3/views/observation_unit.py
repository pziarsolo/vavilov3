from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   ByObjectStudyPermMixin, BulkOperationsMixin)
from vavilov3.models import ObservationUnit
from vavilov3.permissions import ObservationUnitByStudyPermission
from vavilov3.serializers.observation_unit import ObservationUnitSerializer
from vavilov3.entities.observation_unit import ObservationUnitStruct
from vavilov3.filters.observation_unit import ObservationUnitFilter


class ObservationUnitViewSet(ByObjectStudyPermMixin, DynamicFieldsViewMixin,
                             viewsets.ModelViewSet, BulkOperationsMixin):
    lookup_field = "name"
    serializer_class = ObservationUnitSerializer
    queryset = ObservationUnit.objects.all()
    filter_class = ObservationUnitFilter
    permission_classes = (ObservationUnitByStudyPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationUnitStruct
