from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests.io import load_institutes_from_file
from vavilov3.tests import BaseTest
TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class InstituteViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(fpath)

    def test_view_readonly(self):
        list_url = reverse('institute-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['data']['instituteCode'], 'ESP004')
        self.assertEqual(result[0]['data']['name'], 'CRF genebank')

        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['data']['instituteCode'], 'ESP004')
        self.assertEqual(result.json()['data']['name'], 'CRF genebank')

    def test_view_readonly_filter_fields(self):
        list_url = reverse('institute-list')
        list_url = '{}?{}={}'.format(list_url, 'fields', 'code')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['data']['instituteCode'], 'ESP004')
        self.assertTrue('name' not in result[0]['data'])

        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['data']['instituteCode'], 'ESP004')

    def test_create_delete(self):

        list_url = reverse('institute-list')
        api_data = {'data': {'instituteCode': 'ESP005',
                             'name': 'test genebank'},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), api_data)

        # Sending corrupt data should fail and return proper error
        api_data = {'data': {'name': 'test genebank'},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),
                         {'detail': 'instituteCode mandatory'})

        api_data = {'data': {'instituteCode': 'ESP005',
                             'name': 'test genebank'},
                    'metadata': {'group': 'admin'}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),
                         {'detail': 'is_public is mandatory in metadata'})

        # create existing institute sholud fail and return proper error
        with transaction.atomic():
            api_data = {'data': {'instituteCode': 'ESP005',
                                 'name': 'test genebank'},
                        'metadata': {'group': 'admin', 'is_public': True}}
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json(),
                             {'detail': 'ESP005 already exist in db'})

        # test delete
        detail_url = reverse('institute-detail', kwargs={'code': 'ESP005'})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        api_data = {'data': {'instituteCode': 'ESP004',
                             'name': 'test genebank'},
                    'metadata': {'group': 'admin', 'is_public': False}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

    def test_filter(self):
        list_url = reverse('institute-list')
        response = self.client.get(list_url, data={'code': 'eSP004'})
        self.assertFalse(response.json())

        response = self.client.get(list_url, data={'code': 'ESP004'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'code__iexact': 'esp004'})
        self.assertEqual(len(response.json()), 1)
        response = self.client.get(list_url, data={'code__icontain': 'esp'})
        self.assertEqual(len(response.json()), 4)
