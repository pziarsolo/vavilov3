from io import TextIOWrapper

from django.core.exceptions import ValidationError

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action

from vavilov3.views import format_error_message
from vavilov3.models import Institute
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin)
from vavilov3.serializers.institute import InstituteSerializer
from vavilov3.filters.institute import InstituteFilter
from vavilov3.permissions import IsAdminOrReadOnly
from vavilov3.entities.institute import InstituteStruct
from vavilov3.entities.shared import serialize_entity_from_csv


class InstituteViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet,
                       BulkOperationsMixin):
    lookup_field = 'code'
    queryset = Institute.objects.order_by('code')
    serializer_class = InstituteSerializer
    filter_class = InstituteFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    Struct = InstituteStruct

