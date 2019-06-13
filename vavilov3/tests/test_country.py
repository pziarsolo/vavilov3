from os.path import join, abspath, dirname

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_institutes_from_file,
                                    load_accessions_from_file,
                                    load_accessionsets_from_file)
from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


class CountryViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def test_view_readonly(self):
        list_url = reverse('country-list')
        response = self.client.get(list_url, data={'ordering': 'code'})
        result = response.json()
        self.assertEqual(len(result), 100)
        self.assertEqual(result[0]['code'], 'ABW')
        self.assertEqual(result[0]['name'], 'Aruba')

        detail_url = reverse('country-detail', kwargs={'code': 'ESP'})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['code'], 'ESP')
        self.assertEqual(result.json()['name'], 'Spain')

    def test_view_readonly_filter_fields(self):
        list_url = reverse('country-list')
        response = self.client.get(list_url, data={'fields': 'code',
                                                   'limit': 300,
                                                   'ordering': 'code'})
        result = response.json()
        self.assertEqual(len(result), 254)
        self.assertEqual(result[0]['code'], 'ABW')
        self.assertTrue('name' not in result[0])

        detail_url = reverse('country-detail', kwargs={'code': 'ESP'})
        result = self.client.get(detail_url, data={'fields': 'code'})
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['code'], 'ESP')
        self.assertEqual(len(result.json().keys()), 1)

    def test_filter(self):
        list_url = reverse('country-list')

        response = self.client.get(list_url, data={'code': 'ESP'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'name': 'es'})
        self.assertEqual(len(response.json()), 19)

        response = self.client.get(list_url,
                                   data={'only_with_accessions': True,
                                         'fields': 'code,name,num_accessions'})
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0],
                         {'code': 'PER', 'name': 'Peru', 'num_accessions': 3})

        response = self.client.get(list_url,
                                   data={'only_with_accessions': False,
                                         'limit': 10})
        self.assertEqual(len(response.json()), 10)


class CountryStatsTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        accessionsets_fpath = join(TEST_DATA_DIR, 'accessionsets.json')
        load_accessionsets_from_file(accessionsets_fpath)

    def test_stats(self):
        detail_url = reverse('country-detail', kwargs={'code': 'PER'})
        response = self.client.get(detail_url, data={'fields': 'stats_by_taxa,stats_by_institute'})
        result = response.json()
        self.assertEqual(result['stats_by_taxa']['species'],
                         {'Solanum lycopersicum':
                          {'num_accessions': 3, 'num_accessionsets': 2}})

        for stat in result['stats_by_institute']:
            if stat['instituteCode'] == 'ESP004':
                self.assertEqual(stat, {'instituteCode': 'ESP004', 'name': 'CRF genebank',
                                        'num_accessions': 1, 'num_accessionsets': 2})
