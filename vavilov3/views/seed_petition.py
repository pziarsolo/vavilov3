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

from vavilov3.views.shared import DynamicFieldsViewMixin
from vavilov3.permissions import SeedPetitionPermission
from vavilov3.models import SeedPetition
from vavilov3.serializers.seed_petition import SeedPetitionSerializer
from vavilov3.entities.seed_petition import SeedPetitionStruct

SEED_PETITION_CSV_FIELDS = ['PETITION ID', 'NAME', 'TYPE', 'INSTITUTION',
                            'ADDRESS', 'CITY', 'POSTAL_CODE', 'COUNTY',
                            'EMAIL', 'PETITION_DATE', 'AIM', 'COMMENTS',
                            'ACCESSIONS']


class SeepPetitionCSVRenderer(renderers.CSVStreamingRenderer):

    def tablize(self, data, header=None, labels=None):
        yield SEED_PETITION_CSV_FIELDS
        for row in data:
            accessionset = SeedPetitionStruct(row)
            yield accessionset.to_list_representation(SEED_PETITION_CSV_FIELDS)


class SeedPetitionViewSet(DynamicFieldsViewMixin, mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    queryset = SeedPetition.objects.all().order_by('-petition_date')
    serializer_class = SeedPetitionSerializer
    permission_classes = (SeedPetitionPermission,)
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [SeepPetitionCSVRenderer]
