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

from rest_framework.permissions import IsAdminUser
from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from vavilov3.models import Group
from vavilov3.conf.settings import ADMIN_GROUP

UserModel = get_user_model()


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField()


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        permission_classes = (IsAdminUser,)
        model = Group
        fields = ('name',)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'password', 'email', 'first_name',
                  'last_name', 'groups')

    def create(self, validated_data):
        user = UserModel.objects.create(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),

        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super(UserSerializer, self).update(instance, validated_data)


class CRFTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super(CRFTokenObtainPairSerializer, cls).get_token(user)

        # Add custom claims
        token['username'] = user.username
        groups = list(user.groups.all().values_list('name', flat=True))
        token['groups'] = groups
        token['is_staff'] = ADMIN_GROUP in groups

        return token
