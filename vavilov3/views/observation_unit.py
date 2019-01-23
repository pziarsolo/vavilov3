from io import TextIOWrapper

from django.core.exceptions import ValidationError

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action

from vavilov3.views import format_error_message
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   ByObjectStudyPermMixin)
from vavilov3.models import ObservationUnit
from vavilov3.permissions import ObservationUnitByStudyPermission
from vavilov3.entities.shared import serialize_entity_from_csv
from vavilov3.serializers.observation_unit import ObservationUnitSerializer
from vavilov3.entities.observation_unit import ObservationUnitStruct
from vavilov3.filters.observation_unit import ObservationUnitFilter


class ObservationUnitViewSet(ByObjectStudyPermMixin, DynamicFieldsViewMixin,
                             viewsets.ModelViewSet):
    lookup_field = "name"
    serializer_class = ObservationUnitSerializer
    queryset = ObservationUnit.objects.all()
    filter_class = ObservationUnitFilter
    permission_classes = (ObservationUnitByStudyPermission,)
    pagination_class = StandardResultsSetPagination

    @action(methods=['post'], detail=False)
    def bulk(self, request):
        action = request.method
        data = request.data
        if 'multipart/form-data' in request.content_type:
            try:
                fhand = TextIOWrapper(request.FILES['csv'].file,
                                      encoding='utf-8')
            except KeyError:
                msg = 'could not found csv file'
                raise ValidationError(format_error_message(msg))

            data = serialize_entity_from_csv(fhand, ObservationUnitStruct)
        else:
            data = request.data

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
