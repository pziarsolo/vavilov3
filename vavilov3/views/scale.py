
from rest_framework import viewsets, status

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin)
from vavilov3.models import Scale, Observation
from vavilov3.permissions import IsAdminOrReadOnly

from vavilov3.serializers.scale import ScaleSerializer
from vavilov3.entities.scale import ScaleStruct
from vavilov3.filters.scale import ScaleFilter
from rest_framework.response import Response
from vavilov3.views import format_error_message


class ScaleViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet,
                   BulkOperationsMixin):
    lookup_field = 'name'
    serializer_class = ScaleSerializer
    queryset = Scale.objects.all()
    filter_class = ScaleFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    Struct = ScaleStruct

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Observation.objects.filter(observation_variable__scale=instance).count():
            msg = 'Can not delete this scale because there are observations'
            msg += ' associated with it'
            return Response(format_error_message(msg),
                            status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
