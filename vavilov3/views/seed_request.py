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

from rest_framework.settings import api_settings
from rest_framework import viewsets, mixins
from rest_framework_csv import renderers

from rest_framework_simplejwt.authentication import JWTAuthentication

from vavilov3.views.shared import DynamicFieldsViewMixin
from vavilov3.permissions import SeedRequestPermission
from vavilov3.models import SeedRequest
from vavilov3.serializers.seed_request import SeedRequestSerializer
from vavilov3.entities.seed_request import SeedRequestStruct

SEED_REQUEST_CSV_FIELDS = ['REQUEST UID', 'NAME', 'TYPE', 'INSTITUTION',
                           'ADDRESS', 'CITY', 'POSTAL_CODE', 'COUNTY',
                           'EMAIL', 'REQUEST_DATE', 'AIM', 'COMMENTS',
                           'ACCESSIONS']


class SeedRequestCSVRenderer(renderers.CSVStreamingRenderer):

    def tablize(self, data, header=None, labels=None):
        if self.format != 'csv_no_header':
            yield SEED_REQUEST_CSV_FIELDS
        for row in data:
            accessionset = SeedRequestStruct(row)
            yield accessionset.to_list_representation(SEED_REQUEST_CSV_FIELDS)


class SeedRequestCSVRendererNoHeader(SeedRequestCSVRenderer):
    format = 'csv_no_header'


class SeedRequestViewSet(DynamicFieldsViewMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    lookup_field = 'request_uid'
    queryset = SeedRequest.objects.all().order_by('-request_date')
    serializer_class = SeedRequestSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = (SeedRequestPermission,)
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + \
        [SeedRequestCSVRenderer, SeedRequestCSVRendererNoHeader]
