from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin)
from vavilov3.serializers.observation_variable import (
    ObservationVariableSerializer)
from vavilov3.models import ObservationVariable
from vavilov3.permissions import UserGroupObjectPermission
from vavilov3.filters.observation_variable import ObservationVariableFilter
from vavilov3.entities.observation_variable import ObservationVariableStruct


class ObservationVariableViewSet(DynamicFieldsViewMixin,
                                 viewsets.ModelViewSet,
                                 BulkOperationsMixin):
    lookup_field = "name"
    serializer_class = ObservationVariableSerializer
    queryset = ObservationVariable.objects.all()
    filter_class = ObservationVariableFilter
    permission_classes = (UserGroupObjectPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationVariableStruct
