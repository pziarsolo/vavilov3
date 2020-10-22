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

from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from rest_framework import viewsets, status
from rest_framework.settings import api_settings
from rest_framework_csv import renderers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin,
                                   OptionalStreamedListCsvMixin)
from vavilov3.models import Observation
from vavilov3.permissions import ObservationByStudyPermission, is_user_admin
from vavilov3.serializers.observation import ObservationSerializer
from vavilov3.entities.observation import (ObservationStruct, TRAITS_IN_COLUMNS,
                                           CREATE_OBSERVATION_UNITS)
from vavilov3.filters.observation import ObservationFilter
from vavilov3.conf.settings import OBSERVATION_CSV_FIELDS
from vavilov3.views import format_error_message
from vavilov3.serializers.shared import serialize_entity_from_excel
from vavilov3.excel import excel_dict_reader
from vavilov3.entities.tags import GERMPLASM_NUMBER, INSTITUTE_CODE


class PaginatedObservationCSVRenderer(renderers.CSVStreamingRenderer):

    def tablize(self, data, header=None, labels=None):
        if self.format != 'csv_no_header':
            yield OBSERVATION_CSV_FIELDS
        for row in data:
            accession = ObservationStruct(row)
            yield accession.to_list_representation(OBSERVATION_CSV_FIELDS)


class PaginatedObservationCSVRendererNoHeader(PaginatedObservationCSVRenderer):
    format = 'csv_no_header'


class ObservationViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet,
                         BulkOperationsMixin, OptionalStreamedListCsvMixin):
    lookup_field = 'observation_id'
    serializer_class = ObservationSerializer
    queryset = Observation.objects.all().order_by('observation_id')
    filter_class = ObservationFilter
    permission_classes = (ObservationByStudyPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationStruct
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + \
        [PaginatedObservationCSVRenderer, PaginatedObservationCSVRendererNoHeader]
    ordering_fields = ('value', 'observation_variable__name',
                       'observation_unit__accession__germplasm_number',
                       'observation_unit__study__name', 'creation_time',
                       'observation_unit__name', 'observation_id')

    def filter_queryset(self, queryset):
        # It filters by the study permissions. And the observations belong
        # to a observation unit that is in a study
        queryset = super().filter_queryset(queryset)
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return queryset.filter(observation_unit__study__is_public=True).distinct()
        elif is_user_admin(user):
            return queryset
        else:
            try:
                user_groups = user.groups.all()
            except (IndexError, AttributeError):
                user_groups = None
            if user_groups:
                return queryset.filter(Q(observation_unit__study__is_public=True) |
                                       Q(observation_unit__study__group__in=user_groups))
            else:
                return queryset.filter(study__is_public=True)

    @action(methods=['post'], detail=False)
    def bulk(self, request):
        action = request.method
#         prev_time = time()
        try:
            data, conf = serialize_observations_from_request(request)
        except ValueError as error:
            msg = 'Could not read file: {}'.format(error)
            raise ValidationError(format_error_message(msg))

        self.conf = conf
        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({'task_id': serializer.instance.id},
                            status=status.HTTP_200_OK, headers={})

    _conf = None

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, conf):
        self._conf = conf


def _cell_to_str(cell):
    str_value = str(cell.value)
    if cell.ctype == 2 and cell.value == int(cell.value):
        str_value = str_value.split('.')[0]
    return str_value


def parse_traits_in_columns_excel(fhand):
    rows = excel_dict_reader(fhand)
    for row in rows:
        try:
            accession = row.pop('ACCESSION')
        except KeyError:
            raise ValueError('ACCESSION column is mandatory')
        institute_code, germplasm_number = accession.value.split(':')
        try:
            study_cell = row.pop('STUDY')
        except KeyError:
            raise ValueError('STUDY column is mandatory')

        study = _cell_to_str(study_cell)
        for key, cell in row.items():
            str_value = _cell_to_str(cell)
            if str_value == '' or str_value is None:
                continue
            yield {'accession': {GERMPLASM_NUMBER: germplasm_number,
                                 INSTITUTE_CODE: institute_code},
                   'study': study,
                   'observation_variable': key, 'value': str_value}


def serialize_observations_from_request(request):
    conf = None
    if 'multipart/form-data' in request.content_type:
        traits_in_columns = request.data.get(TRAITS_IN_COLUMNS, None)
        create_observation_units = request.data.get(CREATE_OBSERVATION_UNITS, None)
        if traits_in_columns:
            fhand = request.FILES['file'].file
            data = list(parse_traits_in_columns_excel(fhand))

            conf = {TRAITS_IN_COLUMNS: traits_in_columns,
                    CREATE_OBSERVATION_UNITS: create_observation_units}

        else:
            try:
                fhand = request.FILES['file'].file
            except KeyError:
                msg = 'could not found the file'
                raise ValueError(msg)

            data = serialize_entity_from_excel(fhand, ObservationStruct)

    else:
        data = request.data
    return data, conf
