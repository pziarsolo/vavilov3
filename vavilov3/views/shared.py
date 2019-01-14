from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from vavilov3.permissions import (filter_queryset_by_user_group_permissions)


class GroupObjectPermMixin(object):

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return filter_queryset_by_user_group_permissions(queryset,
                                                         self.request.user)


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
