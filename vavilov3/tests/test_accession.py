from copy import deepcopy

from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_accessions_from_file,
                                    load_institutes_from_file,
                                    assert_error_is_equal,
                                    load_studies_from_file,
                                    load_observation_unit_from_file,
                                    load_scales_from_file, load_traits_from_file,
                                    load_observation_variables_from_file,
                                    load_observations_from_file)
from vavilov3.data_io import initialize_db
from vavilov3.views import DETAIL

from vavilov3.entities.tags import DATA_SOURCE

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


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

        list_url = reverse('accession-list')
        response = self.client.get(list_url,
                                   data={'fields': 'instituteCode,passp'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ['Passed fields are not allowed'])

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

    def test_bulk_create_with_errors(self):
        self.add_user_credentials()
        list_url = reverse('accession-list')
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006 11'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007 11'},
                     'metadata': {}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         print(response.json())
#         print(response.status_code)
        return

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
        self.assertEqual(len(response.json()), 1)

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
        aaa = b'PUID,INSTCODE,ACCENUMB,CONSTATUS,IS_AVAILABLE,COLLNUMB'
        bbb = b'ESP004,BGE0001,is_active,True,,,Solanum,lycopersicum,,var. cera'
        ccc = b'YACUCHO;province:HUAMANGA;municipality:Socos;site:Santa Rosa '

        for piece in (aaa, bbb, ccc):
            self.assertIn(piece, content)


class AccessionFilterByObservationsViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        studies_fpath = join(TEST_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)
        fpath = join(TEST_DATA_DIR, 'observation_units.json')
        load_observation_unit_from_file(fpath)

        scale_fpath = join(TEST_DATA_DIR, 'scales.json')
        load_scales_from_file(scale_fpath)

        trait_fpath = join(TEST_DATA_DIR, 'traits.json')
        load_traits_from_file(trait_fpath)

        fpath = join(TEST_DATA_DIR, 'observation_variables.json')
        load_observation_variables_from_file(fpath)

        fpath = join(TEST_DATA_DIR, 'observations.json')
        load_observations_from_file(fpath, obs_group='OBS1', user=self.crf_user)

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('accession-list')

        response = self.client.get(list_url,
                                   data={'Plant size:cm__gt': '4'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'Plant size:cm__gt': '4',
                                         'Plant size:cm__lt': '18'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'Plant size:cm__gt': '4',
                                         'Plant size:cm__lt': '7'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(list_url,
                                   data={'Plant size:cm': '12'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'Plant size:cm': '12',
                                         'Plant Growth type:categorical': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'Plant size:cm__gt': '11',
                                         'Plant Growth type:categorical': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'Plant Growth type:categorical': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class AccessionBulkTooglePublic(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def test_basic_toogle(self):
        self.add_admin_credentials()
        toggle_url = reverse('accession-toggle-public')
        list_url = reverse('accession-list')
        search_params = {'institute_code': 'ESP026'}

        response = self.client.get(list_url, data=search_params)
        self.assertFalse(response.json()[0]['metadata']['is_public'])

        data = {'search_params': search_params, 'public': True}

        response = self.client.post(toggle_url, data=data, format='json')
        self.assertEqual(response.json(), {'detail': ['1 accession made public']})

        response = self.client.get(list_url, data=search_params)
        self.assertTrue(response.json()[0]['metadata']['is_public'])

        self.add_user_credentials()
        response = self.client.post(toggle_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.remove_credentials()
        response = self.client.post(toggle_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bad_requests(self):
        self.add_admin_credentials()
        toggle_url = reverse('accession-toggle-public')

        data = {'public': True}

        response = self.client.post(toggle_url, data=data, format='json')
        self.assertEqual(response.json()['detail'],
                         ['public and search_params keys are mandatory to toogle publc state'])

        data = {'search_params': {}}

        response = self.client.post(toggle_url, data=data, format='json')
        self.assertEqual(response.json()['detail'],
                         ['public and search_params keys are mandatory to toogle publc state'])
