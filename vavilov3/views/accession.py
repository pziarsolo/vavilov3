from io import TextIOWrapper
# from time import time

from rest_framework import viewsets, status
from rest_framework_csv import renderers
from rest_framework.settings import api_settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework.backends import DjangoFilterBackend

from vavilov3.models import Accession
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   MultipleFieldLookupMixin,
                                   GroupObjectPublicPermMixin,
                                   TooglePublicMixim)
from vavilov3.serializers.accession import AccessionSerializer
from vavilov3.filters.accession import AccessionFilter
from vavilov3.permissions import UserGroupObjectPublicPermission
from vavilov3.entities.accession import (AccessionStruct,
                                         AccessionValidationError,
                                         serialize_accessions_from_excel)
from vavilov3.conf.settings import ACCESSION_CSV_FIELDS
from vavilov3.views import format_error_message
from vavilov3.filters.accession_observation_filter_backend import AccessionByObservationFilterBackend
from django.http.response import StreamingHttpResponse


# class PaginatedAccessionCSVRenderer(renderers.CSVRenderer):
class PaginatedAccessionCSVRenderer(renderers.CSVStreamingRenderer):

    def tablize(self, data, header=None, labels=None):
        yield ACCESSION_CSV_FIELDS
        for row in data:
            accession = AccessionStruct(row)
            yield accession.to_list_representation(ACCESSION_CSV_FIELDS)


class AccessionViewSet(MultipleFieldLookupMixin, GroupObjectPublicPermMixin,
                       DynamicFieldsViewMixin, TooglePublicMixim,
                       viewsets.ModelViewSet):
    lookup_fields = ('institute_code', 'germplasm_number')
    lookup_url_kwarg = 'institute_code>[^/]+):(?P<germplasm_number'
    lookup_value_regex = '[^/]+'
    filter_foreignkey_mapping = {'institute_code': 'institute__code'}
    queryset = Accession.objects.all()
    serializer_class = AccessionSerializer
    filter_class = AccessionFilter
    filter_backends = (AccessionByObservationFilterBackend, DjangoFilterBackend)
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedAccessionCSVRenderer]

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
                msg = 'could not found csv file or data_store info'
                raise ValidationError(msg)
            try:
                data = serialize_accessions_from_excel(fhand, data_source_code,
                                                       data_source_kind)
            except AccessionValidationError as error:
                raise ValueError(format_error_message(error))
        else:
            data = request.data
        # prev_time = calc_duration('csv to json', prev_time)

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            # prev_time = calc_duration('get_serializer', prev_time)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            # prev_time = calc_duration('perform_create', prev_time)
            return Response({'task_id': serializer.instance.id},
                            status=status.HTTP_200_OK, headers={})

    def list(self, request, *args, **kwargs):
        csv = True if 'PaginatedAccessionCSVRenderer' in str(request.accepted_renderer) else False
        if csv:
            queryset = self.filter_queryset(self.get_queryset())
            if queryset.count() > 10000:
                serializer = self.get_serializer(queryset, many=True)

                return StreamingHttpResponse(
                    streaming_content=request.accepted_renderer.render(serializer.data),
                    content_type="text/csv")

        return viewsets.ModelViewSet.list(self, request, *args, **kwargs)
