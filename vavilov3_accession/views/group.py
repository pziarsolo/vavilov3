from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from vavilov3_accession.models import Group
from vavilov3_accession.serializers.auth import GroupSerializer

User = get_user_model()


class GroupViewSet(ModelViewSet):
    lookup_field = 'name'
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAdminUser,)

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
