from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3_accession.tests import BaseTest
from vavilov3_accession.data_io import initialize_db
from vavilov3_accession.tests.data_io import (load_institutes_from_file,
                                              load_accessions_from_file,
                                              load_accessionsets_from_file,
                                              assert_error_is_equal)

from vavilov3_accession.entities.tags import (INSTITUTE_CODE, GERMPLASM_NUMBER,
                                              ACCESSIONS)
from vavilov3_accession.views import DETAIL

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class AccessionSetViewTest(BaseTest):

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
        self.add_admin_credentials()
        detail_url = reverse('accessionset-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'accessionset_number': 'NC001'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['instituteCode'], 'ESP004')
        self.assertTrue(response.json()['data']['accessions'])
        self.assertTrue(response.json()['metadata'])

        list_url = reverse('accessionset-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_view_readonly_with_fields(self):
        self.add_admin_credentials()
        detail_url = reverse('accessionset-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'accessionset_number': 'NC001'})
        response = self.client.get(detail_url, data={'fields': 'institute'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ['Passed fields are not allowed'])

        response = self.client.get(detail_url,
                                   data={'fields': 'instituteCode'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['instituteCode'], 'ESP004')
        self.assertEqual(len(response.json()['data'].keys()), 1)

        response = self.client.get(
            detail_url,
            data={'fields': 'instituteCode,accessions,genera'})
        self.assertEqual(response.json()['data']['instituteCode'], 'ESP004')
        self.assertEqual(len(response.json()['data']['accessions']), 2)
        self.assertEqual(len(response.json()['data'].keys()), 3)
        self.assertEqual(response.json()['data']['genera'], ['Solanum'])

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('accessionset-list')
        api_data = {'data': {'instituteCode': 'ESP004',
                             'accessionsetNumber': 'NC003'},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession'])
        api_data = {'data': {'instituteCode': 'ESP004',
                             'accessionsetNumber': 'NC003',
                             ACCESSIONS: [{INSTITUTE_CODE: 'ESP004',
                                           GERMPLASM_NUMBER: 'BGE0004'}]},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json()['data'], api_data['data'])

        # bad payload data
        api_data = {'data': {'instituteCode': 'ESP004'},
                    'metadata': {}}
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['accessionsetNumber mandatory'])

        # already en db
        with transaction.atomic():
            api_data = {'data': {'instituteCode': 'ESP004',
                                 'accessionsetNumber': 'NC003'},
                        'metadata': {}}

            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert_error_is_equal(
                response.json(),
                ['This accessionset already exists in db: ESP004 NC003'])

        detail_url = reverse('accessionset-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'accessionset_number': 'NC003'})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # cano not add accessionset if accessions not in db
        api_data = {'data': {'instituteCode': 'ESP004',
                             'accessionsetNumber': 'NC004',
                             ACCESSIONS: [{INSTITUTE_CODE: 'ESP004',
                                           GERMPLASM_NUMBER: 'fake'}]},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ['NC004: accession not found ESP004:fake'])

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('accessionset-list')

        response = self.client.get(list_url,
                                   data={'accessionset_number': 'NC001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'is_public': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'is_public': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'accessionset_number__icontains': '01'})
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
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'country': 'PER'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'country': 'ESP'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'biological_status': 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('accessionset-list')
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0006'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    {'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0007'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession',
             'can not set group or is public while creating the accession'])
        # correct data
        self.assertEqual(len(self.client.get(list_url).json()), 2)
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        # Should fail, can not add again same item
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)

        self.assertEqual(len(self.client.get(list_url).json()), 4)

    def test_bulk_create_csv(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'accessionsets.csv')
        list_url = reverse('accessionset-list')
        bulk_url = reverse('accessionset-bulk')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 2)
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        # adding again fails with error
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print(response.json())
        self.assertEqual(len(response.json()[DETAIL]), 2)


class AccessionSetPermissionViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        accessionsets_fpath = join(TEST_DATA_DIR, 'accessionsets.json')
        load_accessionsets_from_file(accessionsets_fpath)

    def test_user_permission(self):
        # list public and mine
        self.add_user_credentials()
        list_url = reverse('accessionset-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_not_mine_but_public(self):
        self.add_user_credentials()
        detail_url = reverse('accessionset-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'accessionset_number': 'NC001'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_not_mine_and_not_public(self):
        self.add_user_credentials()
        detail_url = reverse('accessionset-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'accessionset_number': 'NC002'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create(self):
        # users can not create accessionset
        self.add_user_credentials()
        list_url = reverse('accessionset-list')
        api_data = {'data': {'instituteCode': 'ESP004',
                             'accessionsetNumber': 'BGE0005'},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user(self):
        # not public
        detail_url = reverse('accessionset-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'accessionset_number': 'NC002'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # public
        detail_url = reverse('accessionset-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'accessionset_number': 'NC001'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        list_url = reverse('accessionset-list')
        response = self.client.get(list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class AccessionsetCsvTests(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        accessionsets_fpath = join(TEST_DATA_DIR, 'accessionsets.json')
        load_accessionsets_from_file(accessionsets_fpath)

    def test_csv(self):
        list_url = reverse('accessionset-list')
        response = self.client.get(list_url, data={'format': 'csv'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content
        a = b'INSTCODE,ACCESETNUMB,ACCESSIONS\r\n'
        b = b'ESP004,NC001,ESP004:BGE0001;ESP026:BGE0002\r\n'

        for piece in (a, b):
            self.assertIn(piece, content)
