from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from vavilov3.views.shared import (StandardResultsSetPagination,
                                   DynamicFieldsViewMixin)
from vavilov3.models import ObservationImage
from vavilov3.permissions import ObservationByStudyPermission, is_user_admin
from vavilov3.serializers.observation_image import ObservationImageSerializer
from vavilov3.filters.observation_image import ObservationImageFilter
from vavilov3.entities.observation import CREATE_OBSERVATION_UNITS
from vavilov3.utils import extract_files_from_zip
import tempfile
from vavilov3.views import format_error_message


class ObservationImageViewSet(DynamicFieldsViewMixin, ModelViewSet):
    lookup_field = 'observation_image_uid'
    serializer_class = ObservationImageSerializer
    queryset = ObservationImage.objects.all()
    filter_class = ObservationImageFilter
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
#         prev_time = time()
        with tempfile.TemporaryDirectory() as tmp_dir:
            extract_dir = tmp_dir

        data, conf = serialize_observation_images_from_request(request, extract_dir)
        self.conf = conf
        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({'task_id': serializer.instance.id},
                            status=status.HTTP_200_OK, headers={})

#
    _conf = None

    @property
    def conf(self):
        if self._conf is None:
            return {CREATE_OBSERVATION_UNITS: 'foreach_observation'}
        return self._conf

    @conf.setter
    def conf(self, conf):
        self._conf = conf


def serialize_observation_images_from_request(request, tmp_extract_dir):
    conf = None
    if 'multipart/form-data' in request.content_type:
        create_observation_units = request.data.get(CREATE_OBSERVATION_UNITS, None)
        zip_file = request.FILES['file'].file
        print(zip_file)
        try:
            data = list(extract_files_from_zip(zip_file, extract_dir=tmp_extract_dir))
        except ValueError as error:
            raise ValidationError(format_error_message(error))

        conf = {CREATE_OBSERVATION_UNITS: create_observation_units,
                'extraction_dir': tmp_extract_dir}
    else:
        msg = 'Request must be a multipart/form-data request with at least a zip file'
        raise ValidationError(format_error_message(msg))
    return data, conf
