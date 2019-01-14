from os.path import join, abspath, dirname

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_institutes_from_file,
                                    load_accessions_from_file)
from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class DataSourceViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def test_view_readonly(self):
        list_url = reverse('datasource-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['code'], 'CRF')
        self.assertEqual(result[0]['kind'], 'project')

        detail_url = reverse('datasource-detail', kwargs={'code': 'CRF'})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['code'], 'CRF')
        self.assertEqual(result.json()['kind'], 'project')
        self.assertEqual(result.json()['num_passports'], 4)

    def test_view_readonly_filter_fields(self):
        list_url = reverse('datasource-list')
        response = self.client.get(list_url, data={'fields': 'code',
                                                   'limit': 300})
        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['code'], 'CRF')
        self.assertEqual(len(result[0].keys()), 1)

        detail_url = reverse('datasource-detail', kwargs={'code': 'CRF'})
        result = self.client.get(detail_url, data={'fields': 'code'})
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['code'], 'CRF')
        self.assertEqual(len(result.json().keys()), 1)

    def test_filter(self):
        list_url = reverse('datasource-list')

        response = self.client.get(list_url, data={'code': 'CRF'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'kind': 'project'})
        self.assertEqual(len(response.json()), 1)

    def test_stats(self):
        detail_url = reverse('country-detail', kwargs={'code': 'PER'})
        self.client.get(detail_url)
        print('No Data Source stat tests')
