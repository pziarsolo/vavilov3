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

from rest_framework import viewsets, status
from rest_framework_csv import renderers
from rest_framework.settings import api_settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework.backends import DjangoFilterBackend

from vavilov3.models import Accession, Observation
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   MultipleFieldLookupMixin,
                                   GroupObjectPublicPermMixin,
                                   TooglePublicMixim,
                                   OptionalStreamedListCsvMixin,
                                   ListModelMixinWithErrorCheck,
                                   CheckBeforeRemoveMixim)
from vavilov3.serializers.accession import AccessionSerializer
from vavilov3.filters.accession import AccessionFilter
from vavilov3.permissions import UserGroupObjectPublicPermission
from vavilov3.entities.accession import (AccessionStruct,
                                         AccessionValidationError,
                                         serialize_accessions_from_excel)
from vavilov3.conf.settings import ACCESSION_CSV_FIELDS
from vavilov3.views import format_error_message
from vavilov3.filters.accession_observation_filter_backend import AccessionByObservationFilterBackend


# class AccessionCSVRenderer(renderers.CSVRenderer):
class AccessionCSVRenderer(renderers.CSVStreamingRenderer):

    def tablize(self, data, header=None, labels=None):
        yield ACCESSION_CSV_FIELDS
        for row in data:
            accession = AccessionStruct(row)
            yield accession.to_list_representation(ACCESSION_CSV_FIELDS)


class AccessionViewSet(MultipleFieldLookupMixin, GroupObjectPublicPermMixin,
                       DynamicFieldsViewMixin, TooglePublicMixim,
                       ListModelMixinWithErrorCheck,
                       CheckBeforeRemoveMixim, viewsets.ModelViewSet,
                       OptionalStreamedListCsvMixin):
    lookup_fields = ('institute_code', 'germplasm_number')
    lookup_url_kwarg = 'institute_code>[^/]+):(?P<germplasm_number'
    lookup_value_regex = '[^/]+'
    filter_foreignkey_mapping = {'institute_code': 'institute__code'}
    queryset = Accession.objects.all().order_by('germplasm_number')
    serializer_class = AccessionSerializer
    filter_class = AccessionFilter
    filter_backends = (AccessionByObservationFilterBackend, DjangoFilterBackend)
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [AccessionCSVRenderer]
    ordering_fields = ('code', 'institute_code')
    ordering = ('-germplasm_number',)

    @action(methods=['post'], detail=False)
    def bulk(self, request):
        action = request.method
        # prev_time = time()
        data = request.data
        if 'multipart/form-data' in request.content_type:
            try:
                fhand = request.FILES['file'].file
                data_source_code = request.data['data_source_code']
                data_source_kind = request.data['data_source_kind']
            except KeyError:
                msg = 'Could not found excel file or data_store info'
                raise ValidationError(msg)
            try:
                data = serialize_accessions_from_excel(fhand, data_source_code,
                                                       data_source_kind)
            except AccessionValidationError as error:
                raise ValidationError(format_error_message(error))
        else:
            data = request.data
        # prev_time = calc_duration('csv to json', prev_time)

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            # prev_time = calc_duration('get_serializer', prev_time)
            try:
                serializer.is_valid(raise_exception=True)
            except BaseException as errors:
                errors = [error for error in errors.detail if error]
                raise ValidationError(errors)

            self.perform_create(serializer)

            # prev_time = calc_duration('perform_create', prev_time)
            return Response({'task_id': serializer.instance.id},
                            status=status.HTTP_200_OK, headers={})

    def check_before_remove(self, instance):
        if Observation.objects.filter(observation_unit__accession=instance).count():
            msg = 'Can not delete this accession because there are observations'
            msg += ' associated to it'
            return Response(format_error_message(msg),
                            status=status.HTTP_400_BAD_REQUEST)
