from io import TextIOWrapper

from django.core.exceptions import ValidationError

from rest_framework_csv import renderers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, mixins
from rest_framework.settings import api_settings

from vavilov3.views.shared import (GroupObjectPermMixin,
                                   DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   MultipleFieldLookupMixin)

from vavilov3.models import AccessionSet
from vavilov3.permissions import UserGroupObjectPermission
from vavilov3.serializers.accessionset import (
    AccessionSetSerializer, serialize_accessionsets_from_csv)
from vavilov3.filters.accessionset import AccessionSetFilter

from vavilov3.conf.settings import ACCESSIONSET_CSV_FIELDS
from vavilov3.entities.accessionset import AccessionSetStruct
from vavilov3.views import format_error_message
from rest_framework.viewsets import GenericViewSet


class PaginatedAccessionSetCSVRenderer(renderers.CSVRenderer):

    def tablize(self, data, header=None, labels=None):
        yield ACCESSIONSET_CSV_FIELDS
        for row in data:
            accessionset = AccessionSetStruct(row)
            yield accessionset.to_list_representation(ACCESSIONSET_CSV_FIELDS)


class AccessionSetViewSet(MultipleFieldLookupMixin, GroupObjectPermMixin,
                          DynamicFieldsViewMixin,
                          mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          GenericViewSet):
                        # viewsets.ModelViewSet):
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
                msg = 'could not found csv file'
                raise ValidationError(format_error_message(msg))

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
