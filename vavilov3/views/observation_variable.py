from rest_framework import viewsets, status

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin)
from vavilov3.serializers.observation_variable import (
    ObservationVariableSerializer)
from vavilov3.models import ObservationVariable, Observation
from vavilov3.permissions import UserGroupObjectPermission
from vavilov3.filters.observation_variable import ObservationVariableFilter
from vavilov3.entities.observation_variable import ObservationVariableStruct
from rest_framework.response import Response
from vavilov3.views import format_error_message


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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Observation.objects.filter(observation_variable=instance).count():
            msg = 'Can not delete this pbservation variable because there are observations'
            msg += ' associated with it'
            return Response(format_error_message(msg),
                            status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
