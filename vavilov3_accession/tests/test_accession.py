from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3_accession.tests import BaseTest
from vavilov3_accession.tests.io import (load_accessions_from_file,
                                         load_institutes_from_file)
from vavilov3_accession.io import initialize_db
from vavilov3_accession.models import Accession
from copy import deepcopy

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class AccessionViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def test_view_readonly(self):
        self.add_admin_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0001'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['instituteCode'], 'ESP004')
        self.assertTrue(response.json()['data']['passports'])
        self.assertTrue(response.json()['metadata'])

        list_url = reverse('accession-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_view_readonly_with_fields(self):
        self.add_admin_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0001'})
        response = self.client.get(detail_url, data={'fields': 'institute'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), ['Passed fields are not allowed'])

        response = self.client.get(detail_url,
                                   data={'fields': 'instituteCode'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['instituteCode'], 'ESP004')
        self.assertEqual(len(response.json()['data'].keys()), 1)

        response = self.client.get(
            detail_url,
            data={'fields': 'instituteCode,passports,genera'})
        self.assertEqual(response.json()['data']['instituteCode'], 'ESP004')
        self.assertEqual(len(response.json()['data']['passports']), 1)
        self.assertEqual(len(response.json()['data'].keys()), 3)
        self.assertEqual(response.json()['data']['genera'], ['Solanum'])

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('accession-list')
        api_data = {'data': {'instituteCode': 'ESP004',
                             'germplasmNumber': 'BGE0005'},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        api_data = {'data': {'instituteCode': 'ESP004',
                             'germplasmNumber': 'BGE0005'},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json()['data'], api_data['data'])

        # bad payload data
        api_data = {'data': {'instituteCode': 'ESP004'},
                    'metadata': {'group': 'admin', 'is_public': True}}
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            api_data = {'data': {'instituteCode': 'ESP004',
                                 'germplasmNumber': 'BGE0005'},
                        'metadata': {'group': 'admin', 'is_public': True}}

            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0005'})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0001'})
        api_data = {'data': {'instituteCode': 'ESP004',
                             'germplasmNumber': 'BGE0001'},
                    'metadata': {'group': 'admin', 'is_public': False}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # admin can change group
        api_data = {'data': {'instituteCode': 'ESP004',
                             'germplasmNumber': 'BGE0001'},
                    'metadata': {'group': 'userGroup', 'is_public': True}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # Fail changing group if not exists
        api_data = {'data': {'instituteCode': 'ESP004',
                             'germplasmNumber': 'BGE0001'},
                    'metadata': {'group': 'rGroup', 'is_public': True}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('accession-list')

        response = self.client.get(list_url,
                                   data={'germplasm_number': 'BGE0004'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'is_public': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'is_public': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'germplasm_number__icontains': '04'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'group': 'CRF'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(list_url,
                                   data={'group': 'admin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'institute_code': 'ESP004'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'institute_code_icontains': '004'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'institute_code_icontains': 'ESP'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url,
                                   data={'country': 'ESP'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'biological_status': 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'numbers': "toma"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class AccessionPermissionsViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

        acc = Accession.objects.get(germplasm_number='BGE0001')
        acc.is_public = True
        acc.save()

        acc = Accession.objects.get(germplasm_number='BGE0003')
        acc.is_public = True

    def test_user_permission(self):
        # list public and mine
        self.add_user_credentials()
        list_url = reverse('accession-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

    def test_not_mine_but_public(self):
        self.add_user_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0001'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_mine_and_not_public(self):
        self.add_user_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP026',
                                     'germplasm_number': 'BGE0002'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mine_and_public(self):
        self.add_user_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP058',
                                     'germplasm_number': 'BGE0003'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mine_and_not_public(self):
        self.add_user_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0004'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create(self):
        self.add_user_credentials()
        list_url = reverse('accession-list')
        api_data = {'data': {'instituteCode': 'ESP004',
                             'germplasmNumber': 'BGE0005'},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        api_data = {'data': {'instituteCode': 'ESP004',
                             'germplasmNumber': 'BGE0005'},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['metadata'],
                         {'group': 'userGroup', 'is_public': False})

    def test_user_can_not_change_group(self):
        self.add_user_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0004'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        api_data = deepcopy(response.json())
        api_data['metadata']['group'] = 'admin'

        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_user(self):
        # not public
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0004'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # public
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP058',
                                     'germplasm_number': 'BGE0003'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        list_url = reverse('accession-list')
        response = self.client.get(list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
