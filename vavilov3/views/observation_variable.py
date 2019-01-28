from io import TextIOWrapper

from django.core.exceptions import ValidationError

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action

from vavilov3.views import format_error_message
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)
from vavilov3.serializers.observation_variable import (
    ObservationVariableSerializer)
from vavilov3.models import ObservationVariable
from vavilov3.permissions import UserGroupObjectPermission
from vavilov3.filters.observation_variable import ObservationVariableFilter
from vavilov3.entities.shared import serialize_entity_from_csv
from vavilov3.entities.observation_variable import ObservationVariableStruct


class ObservationVariableViewSet(DynamicFieldsViewMixin,
                                 viewsets.ModelViewSet):
    lookup_field = "name"
    serializer_class = ObservationVariableSerializer
    queryset = ObservationVariable.objects.all()
    filter_class = ObservationVariableFilter
    permission_classes = (UserGroupObjectPermission,)
    pagination_class = StandardResultsSetPagination

    @action(methods=['post', 'put', 'patch'], detail=False)
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

            data = serialize_entity_from_csv(fhand, ObservationVariableStruct)
        else:
            data = request.data

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
