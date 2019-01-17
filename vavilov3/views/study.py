from io import TextIOWrapper

from rest_framework import viewsets, status
from rest_framework_csv import renderers
from rest_framework.settings import api_settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   GroupObjectPublicPermMixin)
from vavilov3.models import Study
from vavilov3.permissions import UserGroupObjectPublicPermission
from vavilov3.views import format_error_message
from vavilov3.serializers.study import StudySerializer
from vavilov3.entities.study import StudyStruct, StudyValidationError
from vavilov3.conf.settings import STUDY_CSV_FIELDS
from vavilov3.filters.study import StudyFilter
from vavilov3.entities.shared import serialize_entity_from_csv


class PaginatedStudyCSVRenderer(renderers.CSVRenderer):

    def tablize(self, data, header=None, labels=None):
        yield STUDY_CSV_FIELDS
        for row in data:
            study = StudyStruct(row)
            yield study.to_list_representation(STUDY_CSV_FIELDS)


class StudyViewSet(GroupObjectPublicPermMixin, DynamicFieldsViewMixin,
                   viewsets.ModelViewSet):
    lookup_field = 'name'
    queryset = Study.objects.all()
    serializer_class = StudySerializer
    filter_class = StudyFilter
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedStudyCSVRenderer]

    @action(methods=['post', 'put', 'patch'], detail=False)
    def bulk(self, request, *args, **kwargs):
        action = request.method
        data = request.data
        if 'multipart/form-data' in request.content_type:
            try:
                fhand = TextIOWrapper(request.FILES['csv'].file,
                                      encoding='utf-8')
            except KeyError:
                msg = 'could not found csv file or data_store info'
                raise ValidationError(msg)
            try:
                data = serialize_entity_from_csv(fhand, StudyStruct)
            except StudyValidationError as error:
                raise ValueError(format_error_message(error))
        else:
            data = request.data

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
