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

from django.test.testcases import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient as Client
from rest_framework import status
from rest_framework.reverse import reverse

from vavilov3.models import Group
from vavilov3.conf.settings import ADMIN_GROUP

User = get_user_model()


class GroupViewTest(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin',
                                                   email='p@p.es',
                                                   password='pass')
        self.user = User.objects.create_user(username='user',
                                             email='p@p.es',
                                             password='pass')
        crf_group = Group.objects.create(name=ADMIN_GROUP)
        self.admin.groups.add(crf_group)

        self.crf_token = self.get_token('admin', 'pass')
        self.token = self.get_token('user', 'pass')

    @staticmethod
    def get_token(username, password):
        client = Client()
        response = client.post(reverse('token_obtain_pair'),
                               {'username': username, 'password': password})
        return response.data['access']

    def test_list(self):
        client = Client()
        response = client.get(reverse('group-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = client.get(reverse('group-list'))
        assert response.status_code == status.HTTP_403_FORBIDDEN

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)
        response = client.get(reverse('group-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_create_mod_delete(self):
        client = Client()
        response = client.post(reverse('group-list'), {'name': 'group1'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = client.post(reverse('group-list'), {'name': 'group1'})
        assert response.status_code == status.HTTP_403_FORBIDDEN

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)
        response = client.post(reverse('group-list'), {'name': 'group1'})
        assert response.status_code == status.HTTP_201_CREATED

        response = client.put(reverse('group-detail',
                                      kwargs={'name': 'group1'}),
                              {'name': 'group1_dup'})
        assert response.status_code == status.HTTP_200_OK

        response = client.delete(reverse('group-detail',
                                         kwargs={'name': 'group1_dup'}))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_add_user_group(self):
        client = Client()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)
        response = client.post(reverse('group-list'), {'name': 'group1'})
        assert response.status_code == status.HTTP_201_CREATED

        client.credentials()
        response = client.post(reverse('group-add-user',
                                       kwargs={'name': 'group1'}),
                               {'username': 'user'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)
        response = client.post(reverse('group-add-user',
                                       kwargs={'name': 'group1'}),
                               {'username': 'user'})
        assert response.status_code == status.HTTP_200_OK
        response = client.get(reverse('user-detail',
                                      kwargs={'username': 'user'}))
        assert response.json()['groups'][0]['name'] == 'group1'

        response = client.post(reverse('group-add-user',
                                       kwargs={'name': 'group1'}),
                               {'username': 'use'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = client.post(reverse('group-delete-user',
                                       kwargs={'name': 'group1'}),
                               {'username': 'user'})
        assert response.status_code == status.HTTP_200_OK

        response = client.get(reverse('user-detail',
                                      kwargs={'username': 'user'}))
        assert not response.json()['groups']

        response = client.post(reverse('group-delete-user',
                                       kwargs={'name': 'group1'}),
                               {'username': 'user'})
        assert response.status_code == status.HTTP_200_OK

    def test_signals(self):
        user = User.objects.create_user(username='pep', email='em@ail.es',
                                        password='pass')
        admin_group = Group.objects.get(name=ADMIN_GROUP)
        self.assertFalse(user.is_staff)

        user.groups.add(admin_group)
        self.assertTrue(user.is_staff)

        user.groups.remove(admin_group)
        self.assertEqual(0, user.groups.all().count())
        self.assertFalse(user.is_staff)

        user.groups.add(admin_group)
        self.assertTrue(user.is_staff)
