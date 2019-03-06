from os.path import join, abspath, dirname
from copy import deepcopy

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (assert_error_is_equal,
                                    load_accessions_from_file,
                                    load_institutes_from_file,
                                    load_studies_from_file,
                                    load_observation_unit_from_file,
                                    load_observations_from_file,
                                    load_observation_variables_from_file,
                                    load_scales_from_file, load_traits_from_file)
from vavilov3.data_io import initialize_db
from vavilov3.entities.observation import TRAITS_IN_COLUMNS, \
    CREATE_OBSERVATION_UNITS

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class ObservationViewTest(BaseTest):

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

    def test_read_only(self):
        list_url = reverse('observation-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 2)
        expected = ['observation_id', 'observation_variable',
                    'observation_unit', 'value', 'observer', 'creation_time',
                    'study', 'accession']
        self.assertEqual(list(result[0].keys()), expected)

    def test_readonly_with_fields(self):
        edit_url = reverse('observation-list')
        response = self.client.get(edit_url, data={'fields': 'observation_variable'})
        first = response.json()[0]
        self.assertEqual(list(first.keys()), ['observation_variable'])

        response = self.client.get(edit_url, data={'fields': 'observation_variable,observation_unit'})
        first = response.json()[0]
        self.assertEqual(list(first.keys()), ['observation_variable',
                                              'observation_unit'])

        response = self.client.get(edit_url, data={'fields': 'observer,study,accession'})
        first = response.json()[0]
        self.assertEqual(first, {'observer': 'observer1',
                                 'study': 'study1',
                                 'accession': {'instituteCode': 'ESP004',
                                               'germplasmNumber': 'BGE0001'}})

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('observation-list')
        api_data = {
            'observation_variable': 'Plant size:cm',
            'observation_unit': 'Plant 1',
            'value': '99',
            'observer': 'observer1',
            'creation_time': '1911-12-03 00:23:00',
        }

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_obj_id = response.json()['observation_id']

        # bad data
        bad_api_data = {
            'observation_variable': 'Plant size:cm',
            'value': '99',
            'observer': 'observer1',
            'creation_time': '1911-12-03 00:23:00'}
        response = self.client.post(list_url, data=bad_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['observation_unit mandatory'])

        # adding again should fail
        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('observation-detail',
                             kwargs={"observation_id": created_obj_id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # not valid value
        api_data = {
            'observation_variable': 'Plant size:cm',
            'observation_unit': 'Plant 1',
            'value': '121',
            'observer': 'observer1',
            'creation_time': '1911-12-03 00:23:00',
        }
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),
                         ['Plant 1: Numericl value is bigger than maxim: 121 > 100.0'])

    def test_update(self):
        self.add_admin_credentials()
        list_url = reverse('observation-list')
        response = self.client.get(list_url)
        api_data = response.json()[0]
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': api_data['observation_id']})

        api_data['observation_unit'] = 'Plant 2'

        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result['observation_id'], api_data['observation_id'])
        self.assertEqual(result['value'], api_data['value'])
        self.assertEqual(result['observation_unit'], api_data['observation_unit'])
        api_data['observation_unit'] = 'non existant'

        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['Observation unit non existant does not exist in db'])

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('observation-list')
        response = self.client.get(list_url, data={'value_range_min': '11',
                                                   'value_range_max': '13',
                                                   'observation_variable': 'Plant size:cm'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'value_range_min': '11',
                                                   'observation_variable': 'Plant size:cm'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'value_range_max': '13',
                                                   'observation_variable': 'Plant size:cm'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'value_range_max': '13'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['Can not use value_range filter if not filtered by observation variable'])

        response = self.client.get(list_url, data={
            'value_range_max': '13',
            'observation_variable': 'Plant Growth type:categorical'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ["Used observation_variable's data type is not numeric"])

        response = self.client.get(list_url,
                                   data={'observation_unit': 'Plant 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'observation_unit_contains': 'Plant'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

        response = self.client.get(list_url,
                                   data={'group': 'userGroup'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(list_url,
                                   data={'group': 'admin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

        response = self.client.get(list_url,
                                   data={'study': 'study1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'study': 'Study1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'study_contains': 'study'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

        response = self.client.get(list_url,
                                   data={'study_contains': 'study1111'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(list_url,
                                   data={'accession_number': 'BGE0001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'accession_institute': 'ESP004'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)


class ObservationUnitPermissionsViewTest(BaseTest):

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
        load_observations_from_file(fpath, obs_group='OBS2', user=self.crf_user)

    def test_user_permission_list(self):
        self.add_user_credentials()
        list_url = reverse('observation-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_user_permission_create(self):
        # an autheticated user
        self.add_user_credentials()
        list_url = reverse('observation-list')
        api_data = {
            "observation_variable": "Plant size:m",
            "observation_unit": "Plant 3",
            "value": "1.2",
            "observer": "observer1",
            "creation_time": "1911-12-01 19:23:00"}

        response = self.client.post(list_url, data=api_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_study_not_mine_and_public(self):
        self.add_admin_credentials()
        response = self.client.get(reverse('observation-list'),
                                   data={'group': 'admin',
                                         'is_public': True})
        detail_id = response.json()[0]['observation_id']

        self.add_user_credentials()
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': detail_id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_not_mine_and_private(self):
        self.add_admin_credentials()
        response = self.client.get(reverse('observation-list'),
                                   data={'group': 'admin',
                                         'is_public': False})
        detail_id = response.json()[0]['observation_id']

        self.add_user_credentials()
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': detail_id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data=response.json(), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_mine_and_public(self):
        self.add_user_credentials()
        list_url = reverse('observation-list')
        response = self.client.get(list_url, data={'group': 'userGroup',
                                                   'is_public': True})
        detail_id = response.json()[0]['observation_id']
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': detail_id})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data=response.json(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_study_mine_and_private(self):
        self.add_user_credentials()
        list_url = reverse('observation-list')
        response = self.client.get(list_url, data={'group': 'userGroup',
                                                   'is_public': False})
        detail_id = response.json()[0]['observation_id']
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': detail_id})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data=response.json(),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_can_not_change_study(self):
        self.add_admin_credentials()
        response = self.client.get(reverse('observation-list'),
                                   data={'group': 'userGroup',
                                         'is_public': True})
        detail_id = response.json()[0]['observation_id']
        self.add_user_credentials()
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': detail_id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        api_data = deepcopy(response.json())
        api_data['observation_unit'] = 'Plant 1'

        response = self.client.put(detail_url, data=api_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['Can not change observation unit because this is in a study you dont own: study1'])

    def test_anonymous_user(self):
        # not public
        self.add_admin_credentials()
        response = self.client.get(reverse('observation-list'),
                                   data={'is_public': False})
        detail_id = response.json()[0]['observation_id']

        self.remove_credentials()
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': detail_id})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # public
        self.add_admin_credentials()
        response = self.client.get(reverse('observation-list'),
                                   data={'is_public': True})
        detail_id = response.json()[0]['observation_id']

        self.remove_credentials()
        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': detail_id})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ObservationBulkViewTest(BaseTest):

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

    def xtest_bulk(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'observations_in_columns.xlsx')
        response = self.client.post(reverse('observation-bulk'),
                                    data={'file': open(fpath, mode='rb'),
                                          TRAITS_IN_COLUMNS: True,
                                          CREATE_OBSERVATION_UNITS: 'foreach_observation'})
        print(response.json())
