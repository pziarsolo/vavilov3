import logging
import tempfile
import subprocess
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
from vavilov3.tasks import (extract_files_from_zip, delete_image,
                            add_task_to_user)
from vavilov3.views import format_error_message
from vavilov3.conf.settings import TMP_DIR

logger = logging.getLogger('vavilov.prod')


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
        with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp_dir:
            extract_dir = tmp_dir

        if 'multipart/form-data' in request.content_type:
            create_observation_units = request.data.get(CREATE_OBSERVATION_UNITS, None)
            fhand = request.FILES['file']
            logger.debug('1')
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.zip',
                                             dir=TMP_DIR) as destination:
                for chunk in fhand.chunks():
                    destination.write(chunk)
                destination.flush()

                subprocess.run(['chmod', '777', destination.name])
                task = extract_files_from_zip.apply_async(args=[destination.name,
                                                                extract_dir])
                try:
                    data = task.wait()
                    add_task_to_user(self.request.user, task)
                except ValueError as error:
                    raise ValidationError(format_error_message(str(error)))

        else:
            msg = 'Request must be a multipart/form-data request '
            msg += 'with at least a zip file'
            raise ValidationError(format_error_message(msg))

        self.conf = {CREATE_OBSERVATION_UNITS: create_observation_units,
                     'extraction_dir': extract_dir}

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({'task_id': serializer.instance.id},
                            status=status.HTTP_200_OK, headers={})

#
    _conf = None

    def perform_destroy(self, instance):
        task = delete_image.apply_async(args=[instance.observation_image_uid])
        _ = task.wait()
        add_task_to_user(self.request.user, task)

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
        logger.debug(type(request.FILES['file']))
        logger.debug(request.FILES['file'].name)
        logger.debug(dir(request.FILES['file']))
        logger.debug(type(zip_file))
        logger.debug(dir(zip_file))
        try:
            data = list(extract_files_from_zip(zip_file, extract_dir=tmp_extract_dir,
                                               make_group_writable=True))
        except ValueError as error:
            raise ValidationError(format_error_message(error))

        conf = {CREATE_OBSERVATION_UNITS: create_observation_units,
                'extraction_dir': tmp_extract_dir}
    else:
        msg = 'Request must be a multipart/form-data request with at least a zip file'
        raise ValidationError(format_error_message(msg))
    return data, conf
