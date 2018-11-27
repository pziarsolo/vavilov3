from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3_accession.tests import BaseTest
from vavilov3_accession.tests.io import (load_institutes_from_file,
                                         load_accessions_from_file,
                                         load_accessionsets_from_file,
                                         assert_error_is_equal)
from copy import deepcopy
from vavilov3_accession.io import initialize_db
from vavilov3_accession.views import DETAIL

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
        self.assertEqual(result[0]['instituteCode'], 'ESP004')
        self.assertEqual(result[0]['name'], 'CRF genebank')

        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['instituteCode'], 'ESP004')
        self.assertEqual(result.json()['name'], 'CRF genebank')

    def test_view_readonly_filter_fields(self):
        list_url = reverse('institute-list')
        list_url = '{}?{}={}'.format(list_url, 'fields', 'code')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['instituteCode'], 'ESP004')
        self.assertTrue('name' not in result[0])

        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['instituteCode'], 'ESP004')

    def docs_are_equal(self, response_json, input_doc):

        doc = deepcopy(response_json)
        doc.pop('num_accessions', None)
        doc.pop('num_accessionsets', None)
        doc.pop('stats_by_taxa', None)
        doc.pop('stats_by_country', None)
        self.assertEqual(doc, input_doc)

    def test_create_delete(self):

        list_url = reverse('institute-list')
        api_data = {'instituteCode': 'ESP005',
                    'name': 'test genebank'}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.add_admin_credentials()
        api_data = {'instituteCode': 'ESP005',
                    'name': 'test genebank'}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.docs_are_equal(response.json(), api_data)

        # Sending corrupt data should fail and return proper error
        api_data = {'name': 'test genebank'}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['instituteCode mandatory'])

        # create existing institute sholud fail and return proper error
        with transaction.atomic():
            api_data = {'instituteCode': 'ESP005',
                        'name': 'test genebank'}
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert_error_is_equal(response.json(),
                                  ['ESP005 already exist in db'])

        # test delete
        detail_url = reverse('institute-detail', kwargs={'code': 'ESP005'})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        api_data = {'instituteCode': 'ESP004',
                    'name': 'test genebank'}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.add_admin_credentials()
        api_data = {'instituteCode': 'ESP004',
                    'name': 'test genebank22'}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.docs_are_equal(response.json(), api_data)

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

    def test_bulk_create(self):
        fpath = join(TEST_DATA_DIR, 'institutes.csv')
        bulk_url = reverse('institute-bulk')
        list_url = reverse('institute-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        self.add_admin_credentials()
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 7)

        # adding again fails with error
#         with transaction.atomic():
#             response = self.client.post(bulk_url,
#                                         data={'csv': open(fpath)},
#                                         format=content_type)
#             self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#             self.assertEqual(len(response.json()[DETAIL]), 3)


class InstituteStatsTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        accessionsets_fpath = join(TEST_DATA_DIR, 'accessionsets.json')
        load_accessionsets_from_file(accessionsets_fpath)

    def tests_stats(self):
        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        _ = self.client.get(detail_url)
        print('No tests for institute stats')
#         import pprint
#         pprint.pprint(response.json())
