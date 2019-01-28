
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin)
from vavilov3.models import Observation
from vavilov3.permissions import ObservationByStudyPermission, is_user_admin
from vavilov3.serializers.observation import ObservationSerializer
from vavilov3.entities.observation import ObservationStruct
from vavilov3.filters.observation import ObservationFilter


class ObservationViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet,
                         BulkOperationsMixin):
    lookup_field = 'observation_id'
    serializer_class = ObservationSerializer
    queryset = Observation.objects.all()
    filter_class = ObservationFilter
    permission_classes = (ObservationByStudyPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationStruct

    def filter_queryset(self, queryset):
        # It filters by the study permissions. And the observations belong
        # to a observation unit that is in a study
        queryset = super().filter_queryset(queryset)
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return queryset.filter(observation_unit__study__is_public=True).distinct()
        elif is_user_admin(user):
            return queryset
        else:
            try:
                user_groups = user.groups.all()
            except (IndexError, AttributeError):
                user_groups = None
            if user_groups:
                return queryset.filter(Q(observation_unit__study__is_public=True) |
                                       Q(observation_unit__study__group__in=user_groups))
            else:
                return queryset.filter(study__is_public=True)
