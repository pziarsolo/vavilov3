from os.path import join, abspath, dirname
from copy import deepcopy

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_institutes_from_file,
                                    load_accessions_from_file,
                                    load_accessionsets_from_file,
                                    assert_error_is_equal)

from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


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
        list_url = '{}?{}={}'.format(list_url, 'fields', 'instituteCode')
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
        doc.pop('pdcis', None)

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

        created_api_data = {'instituteCode': 'ESP005', 'name': 'test genebank',
                            'address': None, 'city': None, 'email': None,
                            'manager': None, 'phone': None, 'type': None,
                            'url': None, 'zipcode': None}
        self.docs_are_equal(response.json(), created_api_data)

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

        # create with all fields
        self.add_admin_credentials()
        api_data = {'instituteCode': 'ESP005', 'name': 'test genebank',
                    'address': "rere", 'city': "csdsds", 'email': "email@aasa.es",
                    'manager': "manager", 'phone': "1231231231",
                    'type': "Gobernamental", 'url': 'http://test',
                    'zipcode': '1121231'}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.docs_are_equal(response.json(), api_data)

    def test_update(self):
        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        api_data = {'instituteCode': 'ESP004',
                    'name': 'test genebank'}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.add_admin_credentials()
        api_data = {'instituteCode': 'ESP004', 'name': 'test genebank'}
        response = self.client.put(detail_url, data=api_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_api_data = {'instituteCode': 'ESP004', 'name': 'test genebank',
                             'address': None, 'city': None, 'email': None,
                             'manager': None, 'phone': None, 'type': None,
                             'url': None, 'zipcode': None}
        self.docs_are_equal(response.json(), returned_api_data)

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
        fields = 'instituteCode,name,num_accessions,num_accessionsets,'
        fields += 'stats_by_country,stats_by_taxa,pdcis'
        response = self.client.get(detail_url, data={'fields': fields})

        result = {'instituteCode': 'ESP004',
                  'name': 'CRF genebank',
                  'num_accessions': 2,
                  'num_accessionsets': 2,

                  'stats_by_taxa': {'genus': {'Solanum': {'num_accessions': 2,
                                                          'num_accessionsets': 2}},
                                    'species':
                                        {'Solanum lycopersicum':
                                            {'num_accessions': 2,
                                             'num_accessionsets': 2}},
                                    'variety':
                                        {'Solanum lycopersicum var. cerasiforme':
                                            {'num_accessions': 2,
                                             'num_accessionsets': 2}}}}
        result_stats_by_country = [{'code': 'PER', 'name': 'Peru',
                                    'num_accessions': 1,
                                    'num_accessionsets': 2},
                                   {'code': 'ESP', 'name': 'Spain',
                                    'num_accessions': 1,
                                    'num_accessionsets': 1}]
        response_json = response.json()
        del response_json['pdcis']
        stats_by_country = response_json.pop('stats_by_country')
        for stat_by_country in stats_by_country:
            self.assertIn(stat_by_country, result_stats_by_country)

        self.assertEqual(response_json, result)
