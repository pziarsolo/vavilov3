from io import TextIOWrapper

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action

from vavilov3.views import format_error_message
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)
from vavilov3.models import Observation
from vavilov3.permissions import ObservationByStudyPermission, is_user_admin
from vavilov3.entities.shared import serialize_entity_from_csv
from vavilov3.serializers.observation import ObservationSerializer
from vavilov3.entities.observation import ObservationStruct
from vavilov3.filters.observation import ObservationFilter


class ObservationViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_field = 'observation_id'
    serializer_class = ObservationSerializer
    queryset = Observation.objects.all()
    filter_class = ObservationFilter
    permission_classes = (ObservationByStudyPermission,)
    pagination_class = StandardResultsSetPagination

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

    @action(methods=['post'], detail=False)
    def bulk(self, request):
        action = request.method
        data = request.data
        if 'multipart/form-data' in request.content_type:
            try:
                fhand = TextIOWrapper(request.FILES['csv'].file,
                                      encoding='utf-8')
            except KeyError:
                msg = 'could not found csv file'
                raise ValidationError(format_error_message(msg))

            data = serialize_entity_from_csv(fhand, ObservationStruct)
        else:
            data = request.data

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
