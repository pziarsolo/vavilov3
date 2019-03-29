from os.path import join, abspath, dirname
from copy import deepcopy

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_observation_variables_from_file,
                                    assert_error_is_equal,
                                    load_scales_from_file,
                                    load_traits_from_file)
from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


class ObservationVariableViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()

        scale_fpath = join(TEST_DATA_DIR, 'scales.json')
        load_scales_from_file(scale_fpath)

        trait_fpath = join(TEST_DATA_DIR, 'traits.json')
        load_traits_from_file(trait_fpath)

        fpath = join(TEST_DATA_DIR, 'observation_variables.json')
        load_observation_variables_from_file(fpath)

    def test_read_only(self):
        list_url = reverse('observationvariable-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 3)

        expected = {'name': 'Plant size:cm',
                    'trait': 'Plant size',
                    'description': 'Measure of plant heigth in centimetres',
                    'method': 'by tape', 'scale': 'centimeter'}
        self.assertEqual(result[0]['data'], expected)
        self.assertEqual(result[0]['metadata'], {'group': 'admin'})

    def test_readonly_with_fields(self):
        edit_url = reverse('observationvariable-detail', kwargs={'name': 'Plant size:cm'})
        response = self.client.get(edit_url, data={'fields': 'name'})

        self.assertEqual(response.json()['data'], {'name': 'Plant size:cm'})

        response = self.client.get(edit_url, data={'fields': 'name,description'})
        self.assertEqual(response.json()['data'], {'name': 'Plant size:cm',
                                                   'description': "Measure of plant heigth in centimetres"})

        response = self.client.get(edit_url, data={'fields': 'name,method'})
        self.assertEqual(response.json()['data'], {'name': 'Plant size:cm',
                                                   'method': 'by tape'})

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('observationvariable-list')
        api_data = {
            "data": {
                "name": "Plant size2",
                "trait": "Plant Growth type",
                "description": "Measure of plant heigth",
                "method": "by tape",
                "scale": "centimeter"},
            "metadata": {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # bad data
        bad_api_data = {
            "data": {
                "name": "Plant",
                "description": "Measure of plant heigth",
                "method": "by tape",
                "scale": "centimeter"},
            "metadata": {}}
        response = self.client.post(list_url, data=bad_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['trait mandatory'])

        # adding agian should fail
        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('observationvariable-detail',
                             kwargs={"name": "Plant size2"})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('observationvariable-detail',
                             kwargs={'name': 'Plant size:cm'})

        api_data = {
            'data': {
                'name': 'Plant size:cm',
                'trait': 'Plant Growth type',
                'description': 'Measure of plant heigth',
                'method': 'by tape',
                'scale': 'centimeter'},
            'metadata': {'group': 'admin'}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # admin can change group
        api_data = {
            'data': {
                'name': 'Plant size:cm',
                'trait': 'Plant Growth type',
                'description': 'Measure of plant heigth',
                'method': 'by tape',
                'scale': 'centimeter'},
            'metadata': {'group': 'userGroup'}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # Fail changing group if not exists
        api_data = {
            'data': {
                'name': 'Plant size:cm',
                'trait': 'Plant Growth type',
                'description': 'Measure of plant heigth',
                'method': 'by tape',
                'scale': 'centimeter'},
            'metadata': {'group': 'rGroup'}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ['Provided group does not exist in db: rGroup'])

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('observationvariable-list')
        response = self.client.get(list_url,
                                   data={'name': 'Plant size:cm'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__iexact': 'Plant size:cm'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__icontains': 'Plant size'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        response = self.client.get(list_url,
                                   data={'group': 'userGroup'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'group': 'admin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)


class ObservationVariablePermissionsViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()

        scale_fpath = join(TEST_DATA_DIR, 'scales.json')
        load_scales_from_file(scale_fpath)

        trait_fpath = join(TEST_DATA_DIR, 'traits.json')
        load_traits_from_file(trait_fpath)

        fpath = join(TEST_DATA_DIR, 'observation_variables.json')
        load_observation_variables_from_file(fpath)
        return

    def test_user_permission_create(self):
        # an autheticated user
        self.add_user_credentials()
        list_url = reverse('observationvariable-list')
        api_data = {
            "data": {
                "name": "Plant size2",
                "trait": "Plant Growth type",
                "description": "Measure of plant heigth",
                "method": "by tape",
                "scale": "centimeter"},
            "metadata": {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_mine(self):
        self.add_user_credentials()
        detail_url = reverse('observationvariable-detail',
                             kwargs={'name': 'Plant size:cm'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mine(self):
        self.add_user_credentials()
        detail_url = reverse('observationvariable-detail',
                             kwargs={'name': 'Plant size:m'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data=response.json(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_can_not_change_group(self):
        self.add_user_credentials()
        detail_url = reverse('observationvariable-detail',
                             kwargs={'name': 'Plant size:m'})
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
