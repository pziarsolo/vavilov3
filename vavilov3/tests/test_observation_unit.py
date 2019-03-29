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
                                    load_plants_from_file)
from vavilov3.data_io import initialize_db

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


class ObservationUnitViewTest(BaseTest):

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

    def test_read_only(self):
        list_url = reverse('observationunit-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 2)
        expected = {"name": "Plant 1",
                    "accession": {
                        "instituteCode": "ESP004",
                        "germplasmNumber": "BGE0001"
                    },
                    "level": "plant",
                    "replicate": "0",
                    "study": "study1"}
        fail = True
        for item in result:
            if item['data'] == expected and item['metadata'] == {'group': 'admin'}:
                fail = False
        if fail:
            raise AssertionError()

    def test_readonly_with_fields(self):
        edit_url = reverse('observationunit-detail', kwargs={'name': 'Plant 1'})
        response = self.client.get(edit_url, data={'fields': 'name'})

        self.assertEqual(response.json()['data'], {'name': 'Plant 1'})

        response = self.client.get(edit_url, data={'fields': 'name,study'})
        self.assertEqual(response.json()['data'], {'name': 'Plant 1',
                                                   'study': "study1"})

        response = self.client.get(edit_url, data={'fields': 'name,accession'})
        self.assertEqual(response.json()['data'], {'name': 'Plant 1',
                                                   'accession': {"instituteCode": "ESP004",
                                                                 "germplasmNumber": "BGE0001"}})

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('observationunit-list')
        api_data = {
            "data": {
                "name": "Plant 5",
                "accession": {
                    "instituteCode": "ESP004",
                    "germplasmNumber": "BGE0001"
                },
                "level": "plant",
                "replicate": "0",
                "study": "study1"},
            "metadata": {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # bad data
        bad_api_data = {
            "data": {
                "name": "Plant 5",
                "accession": {
                    "instituteCode": "ESP004",
                    "germplasmNumber": "BGE0001"
                },
                "level": "plant",
                "replicate": "0"},
            "metadata": {}}
        response = self.client.post(list_url, data=bad_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['study mandatory'])

        # adding agian should fail
        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('observationunit-detail',
                             kwargs={"name": "Plant 5"})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 1'})

        api_data = {
            'data': {
                "name": "Plant 1",
                "accession": {
                    "instituteCode": "ESP004",
                    "germplasmNumber": "BGE0001"
                },
                "level": "plant2",
                "replicate": "0",
                "study": "study1"
            },
            'metadata': {}}

        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data'], api_data['data'])

        # admin can change study
        api_data = {
            'data': {
                "name": "Plant 1",
                "accession": {
                    "instituteCode": "ESP004",
                    "germplasmNumber": "BGE0001"
                },
                "level": "plant2",
                "replicate": "0",
                "study": "study2"},
            'metadata': {}}
        response = self.client.put(detail_url, data=api_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data'], api_data['data'])
        self.assertEqual(response.json()['metadata'], {'group': 'admin'})

        # Fail changing study if not exists
        api_data = {
            'data': {
                "name": "Plant 1",
                "accession": {
                    "instituteCode": "ESP004",
                    "germplasmNumber": "BGE0001"
                },
                "level": "plant2",
                "replicate": "0",
                "study": "study22"},
            'metadata': {'group': 'rGroup'}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        assert_error_is_equal(
            response.json(),
            ['The study has not been added yet to the database: study22'])

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('observationunit-list')
        response = self.client.get(list_url, data={'name': 'Plant 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__iexact': 'plant 1'})
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

        response = self.client.get(list_url,
                                   data={'study': 'study1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'study': 'Study1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'study_contains': 'study'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url,
                                   data={'study_contains': 'study1111'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)


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

    def test_user_permission_list(self):
        self.add_user_credentials()
        list_url = reverse('observationunit-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

    def test_user_permission_create(self):
        # an autheticated user
        self.add_user_credentials()
        list_url = reverse('observationunit-list')
        api_data = {
            "data": {"name": "Plant 7",
                     "accession": {
                         "instituteCode": "ESP004",
                         "germplasmNumber": "BGE0001"
                     },
                     "level": "Plant",
                     "replicate": "0",
                     "study": "study3"},
            "metadata": {}}

        response = self.client.post(list_url, data=api_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_study_not_mine_and_public(self):
        self.add_user_credentials()
        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 1'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_not_mine_and_private(self):
        self.add_user_credentials()
        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 2'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data=response.json(), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_mine_and_public(self):
        self.add_user_credentials()
        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 3'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data=response.json(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_study_mine_and_private(self):
        self.add_user_credentials()
        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 4'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data=response.json(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_can_not_change_study(self):
        self.add_user_credentials()
        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 3'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        api_data = deepcopy(response.json())
        api_data['data']['study'] = 'study1'
        api_data['metadata'] = {}

        response = self.client.put(detail_url, data=api_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['Can not change ownership if study does not belong to you : admin'])

    def test_anonymous_user(self):
        # not public
        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 1'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ObservationUnitPlantViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        studies_fpath = join(TEST_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)
        fpath = join(TEST_DATA_DIR, 'plants.json')
        load_plants_from_file(fpath)
        fpath = join(TEST_DATA_DIR, 'observation_units_with_plants.json')
        load_observation_unit_from_file(fpath)

    def test_read_only(self):
        list_url = reverse('observationunit-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 2)
        expected = {"name": "Plant 1",
                    "accession": {
                        "instituteCode": "ESP004",
                        "germplasmNumber": "BGE0001"
                    },
                    "level": "plant",
                    "replicate": "0",
                    "study": "study1",
                    "plants": ["Plant 1"]}
        fail = True
        for item in result:
            if item['data'] == expected and item['metadata'] == {'group': 'admin'}:
                fail = False
        if fail:
            raise AssertionError()

    def test_create_observation_unit_with_plant(self):
        api_data = {
            "data":
                {
                    "name": "Plant 10",
                    "accession": {
                        "instituteCode": "ESP004",
                        "germplasmNumber": "BGE0001"
                    },
                    "level": "plant",
                    "replicate": "0",
                    "study": "study3",
                    "plants": ["Plant 1"]},
            "metadata": {}}

        self.add_user_credentials()
        list_url = reverse('observationunit-list')
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['Can not add plant you dont own to observation unit: Plant 1'])

        self.add_admin_credentials()
        list_url = reverse('observationunit-list')
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        api_data['data']['name'] = 'asa'
        api_data['data']['plants'] = ['asa']
        list_url = reverse('observationunit-list')
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['The given plant does not exist in asa : asa'])

    def test_update_observation_unit_with_plant(self):

        self.add_admin_credentials()
        detail_url = reverse('observationunit-detail', kwargs={'name': 'Plant 1'})
        response = self.client.get(detail_url)
        api_data = response.json()
        api_data['data']['plants'] = ['Plant 1', "Plant 2"]
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.json(), api_data)
        response = self.client.get(detail_url)
        self.assertEqual(response.json(), api_data)

        self.add_user_credentials()
        detail_url = reverse('observationunit-detail', kwargs={'name': 'Plant 3'})
        response = self.client.get(detail_url)

        api_data = response.json()
        api_data['data']['plants'] = ['Plant 3', "Plant 1"]
        response = self.client.put(detail_url, data=api_data, format='json')

        assert_error_is_equal(
            response.json(),
            ['Can not add plant you dont own to observation unit: Plant 1'])

        api_data['data']['plants'] = []
        response = self.client.put(detail_url, data=api_data, format='json')

    def test_plant_filters(self):
        self.add_admin_credentials()
        list_url = reverse('observationunit-list')

        response = self.client.get(list_url, data={'plant': 'Plant 3'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'plant_contains': 'Plant'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)
