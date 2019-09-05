from time import time

from django.http.response import StreamingHttpResponse

from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination

from vavilov3.permissions import (filter_queryset_by_user_group_public_permissions,
                                  filter_queryset_by_study_permissions,
                                  filter_queryset_by_obs_unit_in_study_permissions)
from vavilov3.views import format_error_message
from vavilov3.serializers.shared import serialize_entity_from_excel


def calc_duration(action, prev_time):
    now = time()
    print('{}: Took {} secs'.format(action, round(now - prev_time, 2)))
#     logger.debug('{}: Took {} secs'.format(action, round(now - prev_time, 2)))
    return now


class BulkOperationsMixin(object):

    @action(methods=['post'], detail=False)
    def bulk(self, request):
        action = request.method
#         prev_time = time()
        data = request.data
        if 'multipart/form-data' in request.content_type:
            try:
                fhand = request.FILES['file'].file
            except KeyError:
                msg = 'could not found the file'
                raise ValidationError(format_error_message(msg))
            try:
                data = serialize_entity_from_excel(fhand, self.Struct)
            except ValueError as error:
                msg = 'Could not read file: {}'.format(error)
                raise ValidationError(format_error_message(msg))
        else:
            data = request.data

        if action == 'POST':
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({'task_id': serializer.instance.id},
                            status=status.HTTP_200_OK,
                            headers={})


class GroupObjectPublicPermMixin(object):

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return filter_queryset_by_user_group_public_permissions(queryset,
                                                                self.request.user)


class TooglePublicMixim:

    @action(methods=['post'], detail=False)
    def toggle_public(self, request):
        try:
            is_public = request.data['public']
            search_params = request.data['search_params']
        except KeyError:
            msg = 'public and search_params keys are mandatory to toogle publc state'
            raise ValidationError(format_error_message(msg))
        queryset = self.filter_queryset(self.get_queryset())
        filterset = self.filter_class(search_params, queryset)

        filterset.qs.update(is_public=is_public)

        msg = "{} {} made {}".format(filterset.qs.count(),
                                     self.serializer_class.data_type,
                                     'public' if is_public else 'private')
        return Response(format_error_message(msg), status=status.HTTP_200_OK)


class ByObjectStudyPermMixin(object):

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return filter_queryset_by_study_permissions(queryset, self.request.user)


class ByObservationUnitInStudyPermMixin(object):

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return filter_queryset_by_obs_unit_in_study_permissions(queryset, self.request.user)


class DynamicFieldsViewMixin(object):

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()

        fields = None

        if self.request.method == 'GET':
            query_fields = self.request.query_params.get("fields", None)
            if query_fields:
                fields = tuple(query_fields.split(','))
        kwargs['context'] = self.get_serializer_context()
        kwargs['fields'] = fields

        return serializer_class(*args, **kwargs)


class LinkHeaderPagination(LimitOffsetPagination):
    """ Inform the user of pagination links via response headers, similar to
    what's described in
    https://developer.github.com/guides/traversing-with-pagination/.
    """

    def get_paginated_response(self, data):
        links = []
        for url, label in ((self.get_previous_link(), 'prev'),
                           (self.get_next_link(), 'next')):
            if url is not None:
                links.append('<{}>; rel="{}"'.format(url, label))

        headers = {'Link': ', '.join(links)} if links else {}
        headers['X-Total-Count'] = self.count

        return Response(data, headers=headers)


class StandardResultsSetPagination(LinkHeaderPagination):
    default_limit = 100


class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field
    filtering.
    """

    def get_object(self):
        queryset = self.get_queryset()  # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter_ = {}
        filter_foreignkey_mapping = getattr(self,
                                            'filter_foreignkey_mapping',
                                            {})
        for field in self.lookup_fields:
            if self.kwargs[field]:  # Ignore empty fields.
                if field in filter_foreignkey_mapping:
                    filter_field = filter_foreignkey_mapping[field]
                else:
                    filter_field = field

                filter_[filter_field] = self.kwargs[field]
        obj = get_object_or_404(queryset, **filter_)  # Lookup the object
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj


class OptionalStreamedListCsvMixin():

    def list(self, request, *args, **kwargs):
        if request.accepted_media_type == 'text/csv':
            queryset = self.filter_queryset(self.get_queryset())
            if queryset.count() > 10000:
                serializer = self.get_serializer(queryset, many=True)

                return StreamingHttpResponse(
                    streaming_content=request.accepted_renderer.render(serializer.data),
                    content_type="text/csv")

        return super().list(self, request, *args, **kwargs)


class ListModelMixinWithErrorCheck():

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            try:
                data = list(serializer.data)
            except ValidationError as error:
                errors = [e for e in error.detail['detail']]
                return Response(format_error_message(errors),
                                status=status.HTTP_400_BAD_REQUEST)

            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        try:
            data = list(serializer.data)
        except ValidationError as error:
            errors = [e for e in error.detail['detail']]
            return Response(format_error_message(errors),
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)
