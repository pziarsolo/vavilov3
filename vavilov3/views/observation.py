from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from rest_framework import viewsets
from rest_framework.settings import api_settings
from rest_framework_csv import renderers

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   BulkOperationsMixin)
from vavilov3.models import Observation
from vavilov3.permissions import ObservationByStudyPermission, is_user_admin
from vavilov3.serializers.observation import ObservationSerializer
from vavilov3.entities.observation import ObservationStruct
from vavilov3.filters.observation import ObservationFilter

from vavilov3.conf.settings import OBSERVATION_CSV_FIELDS


class PaginatedObservationCSVRenderer(renderers.CSVRenderer):

    def tablize(self, data, header=None, labels=None):
        yield OBSERVATION_CSV_FIELDS
        for row in data:
            accession = ObservationStruct(row)
            yield accession.to_list_representation(OBSERVATION_CSV_FIELDS)


class ObservationViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet,
                         BulkOperationsMixin):
    lookup_field = 'observation_id'
    serializer_class = ObservationSerializer
    queryset = Observation.objects.all()
    filter_class = ObservationFilter
    permission_classes = (ObservationByStudyPermission,)
    pagination_class = StandardResultsSetPagination
    Struct = ObservationStruct
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PaginatedObservationCSVRenderer]

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
