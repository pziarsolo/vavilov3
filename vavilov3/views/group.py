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

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from vavilov3.models import Group
from vavilov3.serializers.auth import GroupSerializer
from vavilov3.views.shared import StandardResultsSetPagination
from vavilov3.permissions import IsUserAdminGroup

User = get_user_model()


class GroupViewSet(ModelViewSet):
    lookup_field = 'name'
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsUserAdminGroup,)
    pagination_class = StandardResultsSetPagination

    @action(methods=['post'], detail=True)
    def add_user(self, request, name=None):
        username = request.data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': 'user does not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        group = self.get_object()
        user.groups.add(group)
        return Response(GroupSerializer(group).data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def delete_user(self, request, name=None):
        username = request.data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': 'user does not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        group = self.get_object()
        user.groups.remove(group)
        return Response(GroupSerializer(group).data, status=status.HTTP_200_OK)
