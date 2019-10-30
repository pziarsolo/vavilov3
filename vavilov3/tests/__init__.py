#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------
from os.path import join, dirname, abspath

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIClient as Client
from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.models import Group
from vavilov3.conf.settings import ADMIN_GROUP
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseTest(TestCase):

    def initialize(self):
        self.client = Client()
        self.configure_users()

    @staticmethod
    def get_token(username, password):
        client = Client()
        response = client.post(reverse('token_obtain_pair'),
                               {'username': username, 'password': password})
        return response.data['access']

    def configure_users(self):
        self.crf_user = User.objects.create_user(username='admin',
                                                 email='p@p.es',
                                                 password='pass1')

        admin_group = Group.objects.create(name=ADMIN_GROUP)
        self.crf_user.groups.add(admin_group)
#         self.crf_token = self.get_token('crf1', 'pass')

        self.user = User.objects.create_user(username='user',
                                             email='user@p.es',
                                             password='pass')
        user_group = Group.objects.create(name='userGroup')
        self.user.groups.add(user_group)
#         self.user_token = self.get_token('user', 'pass')

    def add_admin_credentials(self):
        token = self.get_token('admin', 'pass1')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def add_user_credentials(self):
        token = self.get_token('user', 'pass')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def remove_credentials(self):
        self.client.credentials()
