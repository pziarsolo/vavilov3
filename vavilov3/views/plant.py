from django.db.models import Q

from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin)
from vavilov3.models import Plant
from vavilov3.permissions import UserGroupObjectPermission, is_user_admin
from vavilov3.serializers.plant import PlantSerializer
from vavilov3.entities.plant import PlantStruct
from vavilov3.filters.plant import PlantFilter
from django.contrib.auth.models import AnonymousUser


class PlantViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet,
                   BulkOperationsMixin):
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
