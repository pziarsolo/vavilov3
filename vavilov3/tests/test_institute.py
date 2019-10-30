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
from vavilov3.conf import settings

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


class InstituteViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        accessionsets_fpath = join(TEST_DATA_DIR, 'accessionsets.json')
        load_accessionsets_from_file(accessionsets_fpath)

    def test_view_readonly(self):
        list_url = reverse('institute-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 7)
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
        self.assertEqual(len(result), 7)
        self.assertEqual(result[0]['instituteCode'], 'ESP004')
        self.assertTrue('name' not in result[0])

        detail_url = reverse('institute-detail', kwargs={'code': 'ESP004'})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['instituteCode'], 'ESP004')

        detail_url = reverse('institute-detail', kwargs={"code": "ESP333"})
        result = self.client.get(detail_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.json()['city'], "Madrid")

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

        # Regular user operations
        # user can retrieve institutes
        self.remove_credentials()
        self.add_user_credentials()
        list_url = reverse('institute-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # user can't add new institutes
        self.remove_credentials()
        self.add_user_credentials()
        api_data = {'instituteCode': 'USER000', 'name': 'user genbank'}
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user can't delete institutes
        detail_url = reverse('institute-detail', kwargs={'code': 'ESP005'})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

        api_data = {'instituteCode': 'ESP004', 'name': 'test genebank',
                    'address': 'Avda Cid', 'city': 'Madrid', 'email': 'esp004@gmail.com',
                    'manager': 'test_manager', 'phone': '6666', 'type': 'governamental',
                    'url': 'esp004.upv.es', 'zipcode': '46960'}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.docs_are_equal(response.json(), api_data)

        # partial update
        api_data = {'instituteCode': 'ESP004', 'name': 'test genebank',
                    'address': 'Avda Cid', 'city': 'Barcelona', 'email': 'esp004@gmail.com',
                    'manager': 'test_manager', 'phone': '6666', 'type': 'governamental',
                    'url': 'esp004.upv.es', 'zipcode': '46960'}
        response = self.client.patch(detail_url, data=api_data, format='json')
        self.docs_are_equal(response.json(), api_data)

        # user can't update institutes
        self.remove_credentials()
        self.add_user_credentials()
        api_data = {'instituteCode': 'ESP004', 'name': 'test genebank'}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user can't partial update institutes
        api_data = {'instituteCode': 'ESP004', 'name': 'test genebank',
                    'city': 'Barcelona'}
        response = self.client.patch(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter(self):
        list_url = reverse('institute-list')
        response = self.client.get(list_url, data={'code': 'eSP004'})
        self.assertFalse(response.json())

        response = self.client.get(list_url, data={'code': 'ESP004'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'code__iexact': 'esp004'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'code__icontains': 'esp'})
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url, data={'name': 'UAC genebank'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'name__iexact': 'uac genebank'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'name__icontains': 'uac'})
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'code_or_name': 'AME'})
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url, data={'code_or_name': 'AME', 'ordering': 'code'})
        self.assertEqual(response.json()[0]['instituteCode'], 'AME0001')

        response = self.client.get(list_url, data={'code_or_name': 'AME', 'ordering': 'name'})
        self.assertEqual(response.json()[0]['instituteCode'], 'USA001')

        response = self.client.get(list_url, data={'code_or_name': 'AME', 'limit': '1'})
        self.assertEqual(len(response.json()), 1)

        for valid_true in settings.VALID_TRUE_VALUES:
            response = self.client.get(list_url, data={'only_with_accessions': valid_true})
            self.assertEqual(len(response.json()), 3)
        for not_valid_true in (False, 'aaa', '2'):
            response = self.client.get(list_url, data={'only_with_accessions': not_valid_true})
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
