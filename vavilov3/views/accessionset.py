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

from rest_framework_csv import renderers
from rest_framework import viewsets
from rest_framework.settings import api_settings

from vavilov3.views.shared import (GroupObjectPublicPermMixin,
                                   DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   MultipleFieldLookupMixin,
                                   BulkOperationsMixin, TooglePublicMixim,
                                   OptionalStreamedListCsvMixin,
                                   ListModelMixinWithErrorCheck)
from vavilov3.models import AccessionSet
from vavilov3.permissions import UserGroupObjectPublicPermission
from vavilov3.serializers.accessionset import AccessionSetSerializer
from vavilov3.filters.accessionset import AccessionSetFilter
from vavilov3.conf.settings import ACCESSIONSET_CSV_FIELDS
from vavilov3.entities.accessionset import AccessionSetStruct


class AccessionSetCSVRenderer(renderers.CSVStreamingRenderer):

    def tablize(self, data, header=None, labels=None):
        if self.format != 'csv_no_header':
            yield ACCESSIONSET_CSV_FIELDS
        for row in data:
            accessionset = AccessionSetStruct(row)
            yield accessionset.to_list_representation(ACCESSIONSET_CSV_FIELDS)


class AccessionSetCSVRendererNoHeader(AccessionSetCSVRenderer):
    format = 'csv_no_header'


class AccessionSetViewSet(MultipleFieldLookupMixin, GroupObjectPublicPermMixin,
                          BulkOperationsMixin, DynamicFieldsViewMixin,
                          ListModelMixinWithErrorCheck,
                          TooglePublicMixim, viewsets.ModelViewSet,
                          OptionalStreamedListCsvMixin):
    lookup_fields = ('institute_code', 'accessionset_number')
    lookup_url_kwarg = 'institute_code>[^/]+):(?P<accessionset_number'
    lookup_value_regex = '[^/]+'
    filter_foreignkey_mapping = {'institute_code': 'institute__code'}
    queryset = AccessionSet.objects.all().order_by('accessionset_number')
    serializer_class = AccessionSetSerializer
    filter_class = AccessionSetFilter
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + \
        [AccessionSetCSVRenderer, AccessionSetCSVRendererNoHeader]
    Struct = AccessionSetStruct
