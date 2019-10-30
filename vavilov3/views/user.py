#
# Copyright (C) 2019 P.Ziarsolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#

from django.contrib.auth import get_user_model

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from vavilov3.serializers.auth import (UserSerializer,
                                       PasswordSerializer)

from vavilov3.models import Group
from vavilov3.permissions import UserPermission
from vavilov3.views.shared import StandardResultsSetPagination

User = get_user_model()


class UserViewSet(ModelViewSet):
    lookup_field = 'username'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (UserPermission,)
    pagination_class = StandardResultsSetPagination

    @action(methods=['post'], detail=True)
    def set_password(self, request, username=None):
        user = self.get_object()
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.data['password'])
            user.save()
            return Response({'status': 'password set'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True)
    def add_group(self, request, username=None):
        group_name = request.data['name']
        try:
            user = self.get_object()
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            return Response()
        except Exception as error:
            return Response({'detail': error},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True)
    def remove_group(self, request, username=None):
        user = self.get_object()
        group_name = request.data['name']

        try:
            group = Group.objects.get(name=group_name)
            user.groups.remove(group)
            return Response('Deleted from group', status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response('User not part of this group',
                            status=status.HTTP_200_OK)
