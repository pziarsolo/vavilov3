from copy import deepcopy

from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_accessions_from_file,
                                    load_institutes_from_file,
                                    assert_error_is_equal)
from vavilov3.data_io import initialize_db
from vavilov3.views import DETAIL
from vavilov3.entities.accession import AccessionStruct
from collections import OrderedDict
from vavilov3.entities.tags import DATA_SOURCE

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
        result = response.json()
        self.assertEqual(result['data']['instituteCode'], 'ESP004')
        self.assertEqual(result['data']['germplasmNumber'], 'BGE0001')
        self.assertEqual(result['data']['is_available'], True)
        self.assertEqual(result['data']['conservation_status'], 'is_active')
        self.assertTrue(result['data']['passports'])
        self.assertEqual(result['data']['passports'][0][DATA_SOURCE],
                         {'code': 'CRF', 'kind': 'project'})
        self.assertTrue(result['metadata'])

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
        assert_error_is_equal(response.json(),
                              ['Passed fields are not allowed'])

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
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession'])
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
        assert_error_is_equal(response.json(), ['germplasmNumber mandatory'])

        with transaction.atomic():
            api_data = {'data': {'instituteCode': 'ESP004',
                                 'germplasmNumber': 'BGE0005'},
                        'metadata': {'group': 'admin', 'is_public': True}}

            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert_error_is_equal(
                response.json(),
                ['can not set group or is public while creating the accession'])

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
        assert_error_is_equal(response.json(),
                              ['Provided group does not exist in db: rGroup'])

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
                                   data={'number_contains': "toma"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'rank': 'genus', 'taxon': 'Zea'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(list_url,
                                   data={'rank': 'genus', 'taxon': 'Solanum'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('accession-list')
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
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
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 6)

        # Should fail, can not add again same item
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)

        self.assertEqual(len(self.client.get(list_url).json()), 6)

    def test_bulk_create_csv(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'accessions.csv')
        list_url = reverse('accession-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 4)
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath),
                                          'data_source_code': 'CRF',
                                          'data_source_kind': 'project'},
                                    format=content_type)
        data_source = response.json()[0]['data']['passports'][0][DATA_SOURCE]
        self.assertEqual(data_source['code'], 'CRF')
        self.assertEqual(data_source['kind'], 'project')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 10)

        result = response.json()[0]
        self.assertEqual(result['data']['instituteCode'], 'ESP004')
        self.assertEqual(result['data']['germplasmNumber'], 'BGE005836')
        self.assertEqual(result['data']['is_available'], False)
        self.assertEqual(result['data']['conservation_status'], 'is_active')

        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE005836'})
        response = self.client.get(detail_url)
        accession = AccessionStruct(response.json())
        del accession.passports[0].data['dataSource']['retrievalDate']
        passport = {'version': '1.0',
                    'taxonomy': {'genus': {'name': 'Zea'},
                                 'species': {'name': 'mays', 'author': 'L.'},
                                 'subspecies': {'name': 'mays'}},
                    'otherNumbers': [{'instituteCode': 'ESP058',
                                      'germplasmNumber': 'CIAM81001'}],
                    'germplasmName': 'Millo do pais',
                    'collectionDate': '19811031',
                    'collectionSite': OrderedDict([('countryOfOriginCode', 'ESP'),
                                                   ('state', 'Galicia'),
                                                   ('province', 'La Coruña'),
                                                   ('municipality', 'Fisterra'),
                                                   ('site', 'Duio,San Martiño'),
                                                   ('latitude', 42.925),
                                                   ('longitude', -9.275),
                                                   ('altitude', 101),
                                                   ('coordUncertainty', '1840')]),
                    'commonCropName': 'Maiz',
                    'germplasmNumber': {'instituteCode': 'ESP004',
                                        'germplasmNumber': 'BGE005836'},
                    'collectionNumber': {'instituteCode': 'ESP058',
                                         'fieldCollectionNumber': '81001'},
                    'collectionSource': '20',
                    'dataSource': {'code': 'CRF', 'kind': 'project'},
                    'biologicalStatusOfAccessionCode': '300'}
        self.assertEqual(accession.passports[0].data, passport)
        # adding again fails with error
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath),
                                          'data_source_code': 'CRF',
                                          'data_source_kind': 'passport_collector'},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 6)


class AccessionPermissionsViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

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
        assert_error_is_equal(response.json(), ['Data key not present'])
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

        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession'])
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

        assert_error_is_equal(
            response.json(),
            ['Can not change ownership if group does not belong to you : admin'])

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

    def test_bulk_create(self):
        self.add_user_credentials()
        list_url = reverse('accession-list')
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # correct data
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
                     'metadata': {}}]
        self.assertEqual(len(self.client.get(list_url).json()), 3)
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 5)

        # Should fail, can not add again same item
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)

        self.assertEqual(len(self.client.get(list_url).json()), 5)


class AccessionCsvTests(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def test_csv(self):
        list_url = reverse('accession-list')
        response = self.client.get(list_url, data={'format': 'csv'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content
        a = b'PUID,INSTCODE,ACCENUMB,CONSTATUS,IS_AVAILABLE,COLLNUMB'
        b = b'ESP004,BGE0001,is_active,True,,,Solanum,lycopersicum,,var. cera'
        c = b'YACUCHO;province:HUAMANGA;municipality:Socos;site:Santa Rosa '

        for piece in (a, b, c):
            self.assertIn(piece, content)
