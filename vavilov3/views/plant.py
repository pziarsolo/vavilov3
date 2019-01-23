from io import TextIOWrapper

from django.core.exceptions import ValidationError
from django.db.models import Q

from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action

from vavilov3.views import format_error_message
from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)
from vavilov3.models import Plant
from vavilov3.permissions import UserGroupObjectPermission, is_user_admin
from vavilov3.entities.shared import serialize_entity_from_csv
from vavilov3.serializers.plant import PlantSerializer
from vavilov3.entities.plant import PlantStruct
from vavilov3.filters.plant import PlantFilter
from django.contrib.auth.models import AnonymousUser


class PlantViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_field = "name"
    serializer_class = PlantSerializer
    queryset = Plant.objects.all()
    filter_class = PlantFilter
    permission_classes = (UserGroupObjectPermission,)
    pagination_class = StandardResultsSetPagination

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

    @action(methods=['post'], detail=False)
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

            data = serialize_entity_from_csv(fhand, PlantStruct)
        else:
            data = request.data

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
