#
# Copyright (C) 2019 P.Ziarsolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#

from rest_framework import viewsets
from rest_framework_csv import renderers
from rest_framework.settings import api_settings

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   GroupObjectPublicPermMixin,
                                   BulkOperationsMixin,
                                   OptionalStreamedListCsvMixin,
                                   CheckBeforeRemoveMixim)
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
                   CheckBeforeRemoveMixim,
                   viewsets.ModelViewSet, BulkOperationsMixin,
                   OptionalStreamedListCsvMixin):
    lookup_field = 'name'
    queryset = Study.objects.all().order_by('name')
    serializer_class = StudySerializer
    filter_class = StudyFilter
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedStudyCSVRenderer]
    Struct = StudyStruct
    ordering = ('name',)
