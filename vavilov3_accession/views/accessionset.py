from io import TextIOWrapper

from django.core.exceptions import ValidationError

from rest_framework_csv import renderers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.settings import api_settings

from vavilov3_accession.views.shared import (GroupObjectPermMixin,
                                             DynamicFieldsViewMixin,
                                             StandardResultsSetPagination,
                                             MultipleFieldLookupMixin)

from vavilov3_accession.models import AccessionSet
from vavilov3_accession.permissions import UserGroupObjectPermission
from vavilov3_accession.serializers.accessionset import (
    AccessionSetSerializer, serialize_accessionsets_from_csv)
from vavilov3_accession.filters.accessionset import AccessionSetFilter

from vavilov3_accession.conf.settings import ACCESSIONSET_CSV_FIELDS
from vavilov3_accession.entities.accessionset import AccessionSetStruct


class PaginatedAccessionSetCSVRenderer(renderers.CSVRenderer):

    def tablize(self, data, header=None, labels=None):
        yield ACCESSIONSET_CSV_FIELDS
        for row in data:
            accessionset = AccessionSetStruct(row)
            yield accessionset.to_list_representation(ACCESSIONSET_CSV_FIELDS)


class AccessionSetViewSet(MultipleFieldLookupMixin, GroupObjectPermMixin,
                          DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_fields = ('institute_code', 'accessionset_number')
    lookup_url_kwarg = 'institute_code>[^/]+):(?P<accessionset_number'
    lookup_value_regex = '[^/]+'
    filter_foreignkey_mapping = {'institute_code': 'institute__code'}
    queryset = AccessionSet.objects.all()
    serializer_class = AccessionSetSerializer
    filter_class = AccessionSetFilter
    permission_classes = (UserGroupObjectPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedAccessionSetCSVRenderer]

    @action(methods=['post', 'put', 'patch'], detail=False)
    def bulk(self, request, *args, **kwargs):
        action = request.method
        data = request.data
        if 'multipart/form-data' in request.content_type:
            try:
                fhand = TextIOWrapper(request.FILES['csv'].file,
                                      encoding='utf-8')
            except KeyError:
                raise ValidationError('could not found csv file')

            data = serialize_accessionsets_from_csv(fhand)
        else:
            data = request.data

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

