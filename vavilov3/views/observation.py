from io import TextIOWrapper

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
                                   BulkOperationsMixin)
from vavilov3.models import Observation
from vavilov3.permissions import ObservationByStudyPermission, is_user_admin
from vavilov3.serializers.observation import ObservationSerializer
from vavilov3.entities.observation import (ObservationStruct, TRAITS_IN_COLUMNS,
                                           CREATE_OBSERVATION_UNITS)
from vavilov3.filters.observation import ObservationFilter
from vavilov3.conf.settings import OBSERVATION_CSV_FIELDS
from vavilov3.views import format_error_message
from vavilov3.serializers.shared import serialize_entity_from_csv
from vavilov3.excel import excel_dict_reader


class PaginatedObservationCSVRenderer(renderers.CSVRenderer):

    def tablize(self, data, header=None, labels=None):
        yield OBSERVATION_CSV_FIELDS
        for row in data:
            accession = ObservationStruct(row)
            yield accession.to_list_representation(OBSERVATION_CSV_FIELDS)


class ObservationViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet,
                         BulkOperationsMixin):
    lookup_field = 'observation_id'
    serializer_class = ObservationSerializer
    queryset = Observation.objects.all()
    filter_class = ObservationFilter
    permission_classes = (ObservationByStudyPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationStruct
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedObservationCSVRenderer]

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
        data, conf = serialize_observations_from_request(request)
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


def parse_traits_in_columns_excel(fhand):
    rows = excel_dict_reader(fhand)
    for row in rows:
        accession = row.pop('Accession', None)
        study = row.pop('Study', None)
        for key, cell in row.items():
            yield {'accession': accession.value, 'study': study.value,
                   'observation_variable': key, 'value': cell.value}


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
                fhand = TextIOWrapper(request.FILES['file'].file,
                                      encoding='utf-8')
            except KeyError:
                msg = 'could not found the file'
                raise ValidationError(format_error_message(msg))

            data = serialize_entity_from_csv(fhand, ObservationStruct)

    else:
        data = request.data
    return data, conf
