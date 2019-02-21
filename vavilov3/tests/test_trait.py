from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import assert_error_is_equal, load_traits_from_file
from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class TraitViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()

        trait_fpath = join(TEST_DATA_DIR, 'traits.json')
        load_traits_from_file(trait_fpath)

    def test_read_only(self):
        list_url = reverse('trait-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 2)

        expected = [
            {"name": "Plant size",
             "description": "Plant size"},
            {"name": "Plant Growth type",
             "description": "Plant Growth type"}]
        self.assertEqual(result, expected)

    def test_readonly_with_fields(self):
        detail_url = reverse('trait-detail', kwargs={'name': 'Plant size'})
        response = self.client.get(detail_url, data={'fields': 'name'})

        self.assertEqual(response.json(), {'name': 'Plant size'})

        response = self.client.get(detail_url, data={'fields': 'name,description'})
        self.assertEqual(response.json(), {'name': 'Plant size',
                                           'description': "Plant size"})

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('trait-list')
        api_data = {
            "name": "fruit color",
            "description": "fruit color",
        }

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # bad data
        bad_api_data = {
            "description": "milimeter"}
        response = self.client.post(list_url, data=bad_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['name mandatory'])

        # adding agian should fail
        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('trait-detail',
                             kwargs={"name": "fruit color"})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('trait-detail',
                             kwargs={'name': 'Plant size'})

        api_data = {
            'name': 'Plant size', 'description': 'centimeter',
        }

        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        response = self.client.get(detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('trait-list')
        response = self.client.get(list_url,
                                   data={'name': 'Plant size'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__icontains': 'plant'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_permissions(self):
        self.add_user_credentials()
        detail_url = reverse('trait-detail', kwargs={'name': 'Plant size'})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        list_url = reverse('trait-list')
        response = self.client.post(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonym_permissions(self):
        detail_url = reverse('trait-detail', kwargs={'name': 'Plant size'})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        list_url = reverse('trait-list')
        response = self.client.post(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
