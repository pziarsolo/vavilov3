from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from vavilov3_accession.conf.settings import USERS_CAN_CREATE_ACCESSIONSETS, \
    ADMIN_GROUP


def _user_is_admin(user):
    if isinstance(user, AnonymousUser):
        return False
    if user.is_staff:
        return True
    if ADMIN_GROUP in user.groups.all().values_list('name', flat=True):
        return True
    return False


class UserPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        action = view.action
        if action in ('list', 'create'):
            return (request.user.is_authenticated and
                    _user_is_admin(request.user))
        elif action in ('retrieve', 'update', 'partial_update', 'destroy',
                        'set_password', 'add_group', 'remove_group'):
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        action = view.action
        if action in ['update', 'partial_update', 'set_password', 'retrieve']:
            return (_user_is_admin(request.user) or
                    (request.user.is_authenticated and
                     obj.id == request.user.id))
        elif action in ('destroy', 'add_group', 'remove_group'):
            return _user_is_admin(request.user)
        return False


class UserGroupObjectPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if (view.action in ('create', 'bulk')):
            if isinstance(request.user, AnonymousUser):
                return False
            elif (not USERS_CAN_CREATE_ACCESSIONSETS and
                  view.basename == 'accessionset' and
                  not request.user.is_staff):
                return False
        elif view.action == 'partial_update' and not request.user.is_staff:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        is_public = obj.is_public
        action = view.action
        user_is_owner = bool(request.user.groups.filter(name=obj.group).count())
        if action in ['retrieve']:
            if (obj.is_public or _user_is_admin(request.user) or
                    user_is_owner):
                return True
        # partial updates only change metadata and it only can be changed by
        # admins
        elif action in ['partial_update'] and _user_is_admin(request.user):
            return True
        elif action in ['update', 'destroy']:
            if (_user_is_admin(request.user) or
               (request.user.is_authenticated and user_is_owner and
                    not is_public)):
                return True

        return False


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, _):
        return (request.method in SAFE_METHODS or
                request.user and _user_is_admin(request.user))


def filter_queryset_by_user_group_permissions(queryset, user):
    # this is the implementation of queryste filtering of
    # UserGroupObjectPermission
    if isinstance(user, AnonymousUser):
        return queryset.filter(is_public=True)
    elif _user_is_admin(user):
        return queryset
    else:
        try:
            user_groups = user.groups.all()
        except (IndexError, AttributeError):
            user_groups = None
        if user_groups:
            return queryset.filter(Q(is_public=True) |
                                   Q(group__in=user_groups))
        else:
            return queryset.filter(is_public=True)
