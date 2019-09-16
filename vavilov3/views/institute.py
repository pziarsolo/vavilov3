from django.db.models.aggregates import Count

from rest_framework import viewsets, status

from vavilov3.models import Institute, Accession
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin,
                                   ListModelMixinWithErrorCheck,
    CheckBeforeRemoveMixim)
from vavilov3.serializers.institute import InstituteSerializer
from vavilov3.filters.institute import InstituteFilter
from vavilov3.permissions import IsAdminOrReadOnly
from vavilov3.entities.institute import InstituteStruct
from rest_framework.response import Response
from vavilov3.views import format_error_message


class InstituteViewSet(DynamicFieldsViewMixin,
                       ListModelMixinWithErrorCheck,
                       CheckBeforeRemoveMixim,
                       viewsets.ModelViewSet,
                       BulkOperationsMixin):
    lookup_field = 'code'
    queryset = Institute.objects
    serializer_class = InstituteSerializer
    filter_class = InstituteFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    Struct = InstituteStruct
    ordering_fields = ('code', 'name', 'by_num_accessions', 'by_num_accessionsets')
    ordering = ('-by_num_accessions',)

    def get_queryset(self):
        return self.queryset.annotate(by_num_accessions=Count('accession', distinct=True),
                                      by_num_accessionsets=Count('accession__accessionset', distinct=True))

    def check_before_remove(self, instance):
        if Accession.objects.filter(institute=instance).count():
            error = 'Can not remove institute, it has accessions associates to it'
            return Response(format_error_message(error),
                            status=status.HTTP_400_BAD_REQUEST)
