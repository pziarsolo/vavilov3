from os.path import join, abspath, dirname
from copy import deepcopy

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (assert_error_is_equal,
                                    load_plants_from_file,
                                    load_institutes_from_file,
                                    load_accessions_from_file,
                                    load_studies_from_file,
                                    load_observation_unit_from_file)
from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class PlantViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        fpath = join(TEST_DATA_DIR, 'plants.json')
        load_plants_from_file(fpath)

    def test_read_only(self):
        list_url = reverse('plant-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 0)

        self.add_user_credentials()
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 2)

        self.add_admin_credentials()
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 4)

    def test_readonly_with_fields(self):
        self.add_admin_credentials()
        edit_url = reverse('plant-detail', kwargs={'name': 'Plant 1'})
        response = self.client.get(edit_url, data={'fields': 'name'})

        self.assertEqual(response.json()['data'], {'name': 'Plant 1'})

        response = self.client.get(edit_url, data={'fields': 'name,x'})
        self.assertEqual(response.json()['data'], {'name': 'Plant 1',
                                                   'x': ""})

        response = self.client.get(edit_url, data={'fields': 'name,entry_number'})
        self.assertEqual(response.json()['data'], {'name': 'Plant 1',
                                                   'entry_number': ''})

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('plant-list')
        api_data = {
            "data": {"name": "Plant size2"},
            "metadata": {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # bad data
        bad_api_data = {
            "data": {
                "description": "Measure of plant heigth",
                "method": "by tape",
                "data_type": "Numerical",
                "unit": "centimeter"},
            "metadata": {}}
        response = self.client.post(list_url, data=bad_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['name mandatory'])

        # adding agian should fail
        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('plant-detail',
                             kwargs={"name": "Plant size2"})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('plant-detail',
                             kwargs={'name': 'Plant 1'})

        response = self.client.get(detail_url)
        api_data = response.json()
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # admin can change group

        api_data['metadata']['group'] = 'userGroup'
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # Fail changing group if not exists
        api_data = {
            'data': {
                'name': 'Plant 1'},
            'metadata': {'group': 'rGroup'}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ['Provided group does not exist in db: rGroup'])

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('plant-list')
        response = self.client.get(list_url,
                                   data={'name': 'Plant 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__iexact': 'Plant 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__icontains': 'Plant'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url,
                                   data={'group': 'userGroup'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'group': 'admin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)


class PlantPermissionsViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        fpath = join(TEST_DATA_DIR, 'plants.json')
        load_plants_from_file(fpath)

    def test_user_permission_create(self):
        # an autheticated user
        self.add_user_credentials()
        list_url = reverse('plant-list')
        api_data = {
            "data": {
                "name": "Plant size2"},
            "metadata": {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_mine(self):
        self.add_user_credentials()
        detail_url = reverse('plant-detail',
                             kwargs={'name': 'Plant 1'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mine(self):
        self.add_user_credentials()
        detail_url = reverse('plant-detail',
                             kwargs={'name': 'Plant 3'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data=response.json(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_can_not_change_group(self):
        self.add_user_credentials()
        detail_url = reverse('plant-detail',
                             kwargs={'name': 'Plant 3'})
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
        detail_url = reverse('observationvariable-detail',
                             kwargs={'name': 'Plant size:cm'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PlantWithObservationUnitTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        fpath = join(TEST_DATA_DIR, 'plants.json')
        load_plants_from_file(fpath)
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        studies_fpath = join(TEST_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)
        fpath = join(TEST_DATA_DIR, 'observation_units_with_plants.json')
        load_observation_unit_from_file(fpath)

    def test_filters(self):
        self.add_admin_credentials()
        list_url = reverse('plant-list')
        response = self.client.get(list_url,
                                   data={'observation_unit': 'Plant 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'study': 'study1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'study_contains': 'study'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url, data={'study_contains': 'studyasda'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(list_url,
                                   data={'observation_unit_contains': 'Plant'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url,
                                   data={'observation_unit_contains': 'Plantasda'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)
