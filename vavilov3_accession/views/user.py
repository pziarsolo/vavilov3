from django.contrib.auth import get_user_model

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from vavilov3_accession.serializers.auth import (UserSerializer,
                                                 PasswordSerializer)

from vavilov3_accession.models import Group
from vavilov3_accession.permissions import UserPermission

User = get_user_model()


class UserViewSet(ModelViewSet):
    lookup_field = 'username'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (UserPermission,)

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
