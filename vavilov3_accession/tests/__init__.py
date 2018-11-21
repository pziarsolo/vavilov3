from os.path import join, dirname, abspath

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIClient as Client
from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3_accession.models import Group
from vavilov3_accession.conf.settings import ADMIN_GROUP


class BaseTest(TestCase):

    def initialize(self):
        self.client = Client()
        self.configure_users()

    @staticmethod
    def get_token(username, password):
        client = Client()
        response = client.post(reverse('vavilov2_auth:token_obtain_pair'),
                               {'username': username, 'password': password})
        return response.data['access']

    def configure_users(self):
        self.crf_user = User.objects.create_user(username='crf1',
                                                 email='p@p.es',
                                                 password='pass')

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
        token = self.get_token('crf1', 'pass')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def add_user_credentials(self):
        token = self.get_token('user', 'pass')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def remove_credentials(self):
        self.client.credentials()
