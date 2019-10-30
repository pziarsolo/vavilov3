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

from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin, CheckBeforeRemoveMixim)
from vavilov3.models import Plant
from vavilov3.permissions import UserGroupObjectPermission, is_user_admin
from vavilov3.serializers.plant import PlantSerializer
from vavilov3.entities.plant import PlantStruct
from vavilov3.filters.plant import PlantFilter
from django.contrib.auth.models import AnonymousUser


class PlantViewSet(DynamicFieldsViewMixin, CheckBeforeRemoveMixim,
                   viewsets.ModelViewSet, BulkOperationsMixin):
    lookup_field = "name"
    serializer_class = PlantSerializer
    queryset = Plant.objects.all()
    filter_class = PlantFilter
    permission_classes = (UserGroupObjectPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = PlantStruct

    def filter_queryset(self, queryset):
        # filter plants by owner and look if they are plublic looing to
        # the observatins units study tahat they belong to
        queryset = super().filter_queryset(queryset)
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return queryset.filter(observation_units__study__is_public=True).distinct()
        elif is_user_admin(user):
            return queryset
        else:
            try:
                user_groups = user.groups.all()
            except (IndexError, AttributeError):
                user_groups = None
            if user_groups:
                return queryset.filter(Q(observation_units__study__is_public=True) |
                                       Q(group__in=user_groups)).distinct()
            else:
                return queryset.filter(observation_units__study__is_public=True).distinct()
