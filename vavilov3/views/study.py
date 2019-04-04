from rest_framework import viewsets
from rest_framework_csv import renderers
from rest_framework.settings import api_settings

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   GroupObjectPublicPermMixin,
                                   BulkOperationsMixin,
                                   OptionalStreamedListCsvMixin)
from vavilov3.models import Study
from vavilov3.permissions import UserGroupObjectPublicPermission
from vavilov3.serializers.study import StudySerializer
from vavilov3.entities.study import StudyStruct
from vavilov3.conf.settings import STUDY_CSV_FIELDS
from vavilov3.filters.study import StudyFilter


class PaginatedStudyCSVRenderer(renderers.CSVStreamingRenderer):

    def tablize(self, data, header=None, labels=None):
        yield STUDY_CSV_FIELDS
        for row in data:
            study = StudyStruct(row)
            yield study.to_list_representation(STUDY_CSV_FIELDS)


class StudyViewSet(GroupObjectPublicPermMixin, DynamicFieldsViewMixin,
                   viewsets.ModelViewSet, BulkOperationsMixin,
                   OptionalStreamedListCsvMixin):
    lookup_field = 'name'
    queryset = Study.objects.all()
    serializer_class = StudySerializer
    filter_class = StudyFilter
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedStudyCSVRenderer]
    Struct = StudyStruct
