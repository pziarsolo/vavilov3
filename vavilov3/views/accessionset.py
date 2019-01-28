from rest_framework_csv import renderers
from rest_framework import mixins
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from vavilov3.views.shared import (GroupObjectPublicPermMixin,
                                   DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   MultipleFieldLookupMixin,
                                   BulkOperationsMixin)
from vavilov3.models import AccessionSet
from vavilov3.permissions import UserGroupObjectPublicPermission
from vavilov3.serializers.accessionset import AccessionSetSerializer
from vavilov3.filters.accessionset import AccessionSetFilter
from vavilov3.conf.settings import ACCESSIONSET_CSV_FIELDS
from vavilov3.entities.accessionset import AccessionSetStruct


class PaginatedAccessionSetCSVRenderer(renderers.CSVRenderer):

    def tablize(self, data, header=None, labels=None):
        yield ACCESSIONSET_CSV_FIELDS
        for row in data:
            accessionset = AccessionSetStruct(row)
            yield accessionset.to_list_representation(ACCESSIONSET_CSV_FIELDS)


class AccessionSetViewSet(MultipleFieldLookupMixin, GroupObjectPublicPermMixin,
                          BulkOperationsMixin,
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
    permission_classes = (UserGroupObjectPublicPermission,)
    pagination_class = StandardResultsSetPagination
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedAccessionSetCSVRenderer]
    Struct = AccessionSetStruct
