from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import assert_error_is_equal, load_scales_from_file
from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class ScaleViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()

        scale_fpath = join(TEST_DATA_DIR, 'scales.json')
        load_scales_from_file(scale_fpath)

    def test_read_only(self):
        list_url = reverse('scale-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 3)

        expected = {'name': 'centimeter', 'description': 'centimeter',
                    'decimal_places': 2, 'data_type': 'Numerical',
                    'min': 0.0, 'max': 100.0, 'valid_values': []}
        self.assertEqual(result[0], expected)
        expected2 = {'name': 'grow type', 'description': 'Grow Type',
                     'decimal_places': None, 'data_type': 'Nominal',
                     'min': None, 'max': None, 'valid_values': ['big', 'small']}

        self.assertEqual(result[2], expected2)

    def test_readonly_with_fields(self):
        detail_url = reverse('scale-detail', kwargs={'name': 'centimeter'})
        response = self.client.get(detail_url, data={'fields': 'name'})

        self.assertEqual(response.json(), {'name': 'centimeter'})

        response = self.client.get(detail_url, data={'fields': 'name,description'})
        self.assertEqual(response.json(), {'name': 'centimeter',
                                           'description': "centimeter"})

        response = self.client.get(detail_url, data={'fields': 'name,data_type'})
        self.assertEqual(response.json(), {'name': 'centimeter',
                                           'data_type': 'Numerical'})

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('scale-list')
        api_data = {
            "name": "milimeter",
            "description": "milimeter",
            "data_type": "Numerical",
            "decimal_places": 0,
            "max": 0, "min": 0,
        }

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # bad data
        bad_api_data = {
            "name": "milimeter",
            "description": "milimeter",
            "decimal_places": 0,
            "max": 0, "min": 0}
        response = self.client.post(list_url, data=bad_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['data_type mandatory'])

        # adding agian should fail
        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('scale-detail',
                             kwargs={"name": "milimeter"})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('scale-detail',
                             kwargs={'name': 'centimeter'})

        api_data = {
            'name': 'centimeter', 'description': 'centimeter',
            'decimal_places': 4, 'data_type': 'Numerical',
            'min': 0.0, 'max': 100.0, 'valid_values': []
        }

        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        response = self.client.get(detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('scale-list')
        response = self.client.get(list_url,
                                   data={'name': 'centimeter'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__icontains': 'meter'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_permissions(self):
        self.add_user_credentials()
        detail_url = reverse('scale-detail', kwargs={'name': 'centimeter'})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        list_url = reverse('scale-list')
        response = self.client.post(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonym_permissions(self):
        detail_url = reverse('scale-detail', kwargs={'name': 'centimeter'})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        list_url = reverse('scale-list')
        response = self.client.post(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
