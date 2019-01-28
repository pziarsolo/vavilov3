from io import TextIOWrapper

from rest_framework import viewsets, status
from rest_framework_csv import renderers
from rest_framework.settings import api_settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from vavilov3.models import Accession
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   MultipleFieldLookupMixin,
                                   GroupObjectPublicPermMixin)
from vavilov3.serializers.accession import (
    AccessionSerializer, serialize_accessions_from_csv)
from vavilov3.filters.accession import AccessionFilter
from vavilov3.permissions import UserGroupObjectPublicPermission
from vavilov3.entities.accession import AccessionStruct, \
    AccessionValidationError
from vavilov3.conf.settings import ACCESSION_CSV_FIELDS
from vavilov3.views import format_error_message


class PaginatedAccessionCSVRenderer(renderers.CSVRenderer):

    def tablize(self, data, header=None, labels=None):
        yield ACCESSION_CSV_FIELDS
        for row in data:
            accession = AccessionStruct(row)
            yield accession.to_list_representation(ACCESSION_CSV_FIELDS)


class AccessionViewSet(MultipleFieldLookupMixin, GroupObjectPublicPermMixin,
                       DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_fields = ('institute_code', 'germplasm_number')
    lookup_url_kwarg = 'institute_code>[^/]+):(?P<germplasm_number'
    lookup_value_regex = '[^/]+'
    filter_foreignkey_mapping = {'institute_code': 'institute__code'}
    queryset = Accession.objects.all()
    serializer_class = AccessionSerializer
    filter_class = AccessionFilter
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedAccessionCSVRenderer]

    @action(methods=['post'], detail=False)
    def bulk(self, request):
        action = request.method
        data = request.data
        if 'multipart/form-data' in request.content_type:
            try:
                fhand = TextIOWrapper(request.FILES['csv'].file,
                                      encoding='utf-8')
                data_source_code = request.data['data_source_code']
                data_source_kind = request.data['data_source_kind']
            except KeyError:
                msg = 'could not found csv file or data_store info'
                raise ValidationError(msg)
            try:
                data = serialize_accessions_from_csv(fhand, data_source_code,
                                                     data_source_kind)
            except AccessionValidationError as error:
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
