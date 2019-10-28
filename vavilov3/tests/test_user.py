from django.test.testcases import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient as Client
from rest_framework import status
from rest_framework.reverse import reverse
from vavilov3.models import Group
from vavilov3.conf.settings import ADMIN_GROUP

User = get_user_model()


class UserViewTest(TestCase):

    @staticmethod
    def get_token(username, password):
        client = Client()
        response = client.post(reverse('token_obtain_pair'),
                               {'username': username, 'password': password})
        return response.data['access']

    def setUp(self):
        self.crf_user = User.objects.create_user(username='crf1',
                                                 email='p@p.es',
                                                 password='pass')

        crf_group = Group.objects.create(name=ADMIN_GROUP)
        self.crf_user.groups.add(crf_group)
        self.crf_token = self.get_token('crf1', 'pass')

        self.user = User.objects.create_user(username='user',
                                             email='user@p.es',
                                             password='pass')

        self.user_token = self.get_token('user', 'pass')

    def remove_token(self, request):
        pass

    def test_list(self):
        client = Client()
        response = client.get(reverse('user-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)

        response = client.get(reverse('user-list'))
        assert response.status_code == status.HTTP_200_OK
        client.credentials()

        # Normal User
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.user_token)
        response = client.get(reverse('user-list'))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_change_delete(self):
        client = Client()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)

        response = client.post(reverse('user-list'),
                               {'username': 'user2', 'email': 'p2@p.es',
                                'password': 'pass'})
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(username='user')
        user_id = user.id
        new_email = 'p3@p.es'
        response = client.patch(reverse('user-detail',
                                        kwargs={'username': user.username}),
                                {'email': new_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(username='user')
        assert user.email == new_email
        client.credentials()

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)
        response = client.patch(reverse('user-detail',
                                kwargs={'username': user.username}),
                                {'email': 'p4@p.es',
                                 'first_name': "jabato",
                                 'last_name': 333,
                                 'failable_test_field': "test",
                                 'id': 3,
                                 })
        assert response.status_code == 200
        user = User.objects.get(username='user')
        # Readonly parameters can't be changed
        assert user.id == user_id

        assert type(user.last_name) == str
        assert user.first_name == "jabato"
        assert user.email == "p4@p.es"

        token = self.get_token('user', 'pass')
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        # user can see itself
        response = client.get(reverse('user-detail',
                                      kwargs={'username': user.username}))
        assert response.status_code == status.HTTP_200_OK

        # user can change password
        url = reverse('user-set-password',
                      kwargs={'username': user.username})
        response = client.post(url, {'password': 'pass2'})
        assert response.status_code == 200

        # user can not destroy its user
        response = client.delete(reverse('user-detail',
                                         kwargs={'username': user.username}))
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # any user can not see user list
        response = client.get(reverse('user-list'))
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # user can not create other user
        response = client.post(reverse('user-list'),
                               {'username': 'test2', 'email': 'p4@p.es',
                                'password': 'pass'})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        client.credentials()

        #
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)
        # admin can change password
        url = reverse('user-set-password',
                      kwargs={'username': user.username})
        response = client.post(url, {'password': 'pass3'})
        assert response.status_code == status.HTTP_200_OK

        # admin can add user to group
        url = reverse('user-add-group',
                      kwargs={'username': user.username})
        group = Group.objects.create(name='test')

        response = client.post(url, data={'name': group.name})
        assert response.status_code == status.HTTP_200_OK

        # admin can delete user
        url = reverse('user-detail',
                      kwargs={'username': user.username})
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # admin can change his own password
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.crf_token)
        url = reverse('user-set-password',
                      kwargs={'username': 'crf1'})
        response = client.post(url, {'password': 'newpass'})
        assert response.status_code == 200

