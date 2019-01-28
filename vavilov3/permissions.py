from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from vavilov3.conf.settings import USERS_CAN_CREATE_ACCESSIONSETS, ADMIN_GROUP


def is_user_admin(user):
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
                    is_user_admin(request.user))
        elif action in ('retrieve', 'update', 'partial_update', 'destroy',
                        'set_password', 'add_group', 'remove_group'):
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        action = view.action
        if action in ['update', 'partial_update', 'set_password', 'retrieve']:
            return (is_user_admin(request.user) or
                    (request.user.is_authenticated and
                     obj.id == request.user.id))
        elif action in ('destroy', 'add_group', 'remove_group'):
            return is_user_admin(request.user)
        return False


class UserGroupObjectPublicPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if (view.action in ('create', 'bulk')):
            if isinstance(request.user, AnonymousUser):
                return False

            elif (not USERS_CAN_CREATE_ACCESSIONSETS and
                  view.basename == 'accessionset' and
                  not is_user_admin(request.user)):
                return False
        elif view.action == 'partial_update' and not is_user_admin(request.user):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        is_public = obj.is_public
        action = view.action
        user_is_owner = bool(request.user.groups.filter(name=obj.group).count())
        if action in ['retrieve']:
            if (obj.is_public or is_user_admin(request.user) or
                    user_is_owner):
                return True
        # partial updates only change metadata and it only can be changed by
        # admins
        elif action in ['partial_update'] and is_user_admin(request.user):
            return True
        elif action in ['update', 'destroy']:
            if (is_user_admin(request.user) or
               (request.user.is_authenticated and user_is_owner and
                    not is_public)):
                return True

        return False


class ByStudyPermission(permissions.BasePermission):

    def get_object_study(self, obj):
        raise NotImplementedError('You need the function toget the study from instance')

    def has_permission(self, request, view):
        if (view.action in ('create', 'bulk')):
            if isinstance(request.user, AnonymousUser):
                return False
        elif view.action == 'partial_update' and not is_user_admin(request.user):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        study = self.get_object_study(obj)
        is_public = study.is_public
        group = study.group
        action = view.action
        user_is_owner = bool(request.user.groups.filter(name=group.name).count())
        if action in ['retrieve']:
            if (is_public or is_user_admin(request.user) or
                    user_is_owner):
                return True
        # partial updates only change metadata and it only can be changed by
        # admins
        elif action in ['partial_update'] and is_user_admin(request.user):
            return True
        elif action in ['update', 'destroy']:
            if (is_user_admin(request.user) or
               (request.user.is_authenticated and user_is_owner)):
                return True

        return False


class ObservationUnitByStudyPermission(ByStudyPermission):

    def get_object_study(self, obj):
        return obj.study


class ObservationByStudyPermission(ByStudyPermission):

    def get_object_study(self, obj):
        return obj.observation_unit.study


class UserGroupObjectPermission(UserGroupObjectPublicPermission):

    def has_object_permission(self, request, view, obj):
        action = view.action
        user_is_owner = bool(request.user.groups.filter(name=obj.group).count())
        if action in ['retrieve']:
            return True
        # partial updates only change metadata and it only can be changed by
        # admins
        elif action in ['partial_update'] and is_user_admin(request.user):
            return True
        elif action in ['update', 'destroy']:
            if (is_user_admin(request.user) or
               (request.user.is_authenticated and user_is_owner)):
                return True

        return False


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, _):
        return (request.method in SAFE_METHODS or
                request.user and is_user_admin(request.user))


def filter_queryset_by_user_group_public_permissions(queryset, user):
    # this is the implementation of queryste filtering of
    # UserGroupObjectPublicPermission
    if isinstance(user, AnonymousUser):
        return queryset.filter(is_public=True)
    elif is_user_admin(user):
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


def filter_queryset_by_study_permissions(queryset, user):
        # this is the implementation of queryste filtering of
    # UserGroupObjectPublicPermission
    if isinstance(user, AnonymousUser):
        return queryset.filter(study__is_public=True).distinct()
    elif is_user_admin(user):
        return queryset
    else:
        try:
            user_groups = user.groups.all()
        except (IndexError, AttributeError):
            user_groups = None
        if user_groups:
            return queryset.filter(Q(study__is_public=True) |
                                   Q(study__group__in=user_groups))
        else:
            return queryset.filter(study__is_public=True)


def filter_queryset_by_obs_unit_in_study_permissions(queryset, user):
        # this is the implementation of queryste filtering of
    # UserGroupObjectPublicPermission
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
