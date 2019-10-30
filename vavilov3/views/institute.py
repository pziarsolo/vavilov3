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
