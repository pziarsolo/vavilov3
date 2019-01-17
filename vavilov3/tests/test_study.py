from os.path import join, abspath, dirname

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.data_io import initialize_db
from vavilov3.views import DETAIL
from vavilov3.tests.data_io import (load_studies_from_file,
                                    assert_error_is_equal)
from copy import deepcopy

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class StudyViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()

        studies_fpath = join(TEST_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)

    def test_view_readonly(self):
        self.add_admin_credentials()
        detail_url = reverse('study-detail', kwargs={'name': 'study1'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        expected = {'data': {'name': 'study1', 'description': 'description1',
                             'active': False, 'start_date': '17/01/2017',
                             'end_date': '01/12/2017', 'location': 'Valencia',
                             'contacts': 'Alguien'},
                    'metadata': {'group': 'admin', 'is_public': True}}
        self.assertEqual(result, expected)

        list_url = reverse('study-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_view_readonly_with_fields(self):
        self.add_admin_credentials()
        detail_url = reverse('study-detail', kwargs={'name': 'study1'})
        response = self.client.get(detail_url, data={'fields': 'institute'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ['Passed fields are not allowed'])

        response = self.client.get(detail_url,
                                   data={'fields': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['name'], 'study1')
        self.assertEqual(len(response.json()['data'].keys()), 1)

        response = self.client.get(
            detail_url,
            data={'fields': 'name,description,active'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['name'], 'study1')
        self.assertEqual(response.json()['data']['description'], 'description1')
        self.assertEqual(response.json()['data']['active'], False)
        self.assertEqual(len(response.json()['data'].keys()), 3)

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('study-list')
        api_data = {'data': {'name': 'study3',
                             'description': 'description3',
                             'active': True},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the study'])

        api_data = {'data': {'name': 'study8',
                             'description': 'description3',
                             'active': True},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data'], api_data['data'])

        api_data = {'data': {'name': 'study8',
                             'description': 'description3'},
                    'metadata': {}}
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['active mandatory'])

        with transaction.atomic():
            api_data = {'data': {'name': 'study3',
                                 'description': 'description3',
                                 'active': True},
                        'metadata': {'group': 'admin', 'is_public': True}}

            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert_error_is_equal(
                response.json(),
                ['can not set group or is public while creating the study'])

        detail_url = reverse('study-detail', kwargs={'name': 'study3'})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('study-detail', kwargs={'name': 'study1'})
        api_data = {'data': {'name': 'study1',
                             'description': 'description1',
                             'active': True},
                    'metadata': {'group': 'admin', 'is_public': True}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        api_data = {'data': {'name': 'study1',
                             'description': 'description1',
                             'active': True},
                    'metadata': {'group': 'userGroup', 'is_public': True}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # Fail changing group if not exists
        api_data = {'data': {'name': 'study1',
                             'description': 'description1',
                             'active': True},
                    'metadata': {'group': 'rGroup', 'is_public': True}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ['Provided group does not exist in db: rGroup'])

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('study-list')

        response = self.client.get(list_url, data={'name': 'study1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'name_contains': 'study'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url, data={'description_icontains': 'description'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        response = self.client.get(list_url, data={'is_active': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

        response = self.client.get(list_url, data={'is_active': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url, data={'is_public': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('study-list')
        api_data = [{'data': {'name': 'study4',
                              'description': 'BGE0006',
                              'active': True},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    {'data': {'name': 'study5', 'description': 'BGE0006',
                              'active': True},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the study',
             'can not set group or is public while creating the study'])

        # correct data
        api_data = [{'data': {'name': 'study5', 'description': 'BGE0006',
                              'active': True},
                     'metadata': {}},
                    {'data': {'name': 'study6', 'description': 'BGE0006',
                              'active': True},
                     'metadata': {}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 6)

        # Should fail, can not add again same item
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)
        self.assertEqual(len(self.client.get(list_url).json()), 6)

    def test_bulk_create_csv(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'studies.csv')
        list_url = reverse('study-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(len(self.client.get(list_url).json()), 6)

        self.assertEqual(response.json()[0]['data']['name'], 'study6')
        self.assertEqual(response.json()[1]['data']['name'], 'study7')

        # adding again fails with error
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)


class StudyPermissionsViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        studies_fpath = join(TEST_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)

    def test_user_permission(self):
        # list public and mine
        self.add_user_credentials()
        list_url = reverse('study-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

    def test_not_mine_but_public(self):
        self.add_user_credentials()
        detail_url = reverse('study-detail',
                             kwargs={'name': 'study1'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_mine_and_not_public(self):
        self.add_user_credentials()
        detail_url = reverse('study-detail',
                             kwargs={'name': 'study2'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mine_and_public(self):
        self.add_user_credentials()
        detail_url = reverse('study-detail',
                             kwargs={'name': 'study3'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mine_and_not_public(self):
        self.add_user_credentials()
        detail_url = reverse('study-detail',
                             kwargs={'name': 'study4'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['Data key not present'])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create(self):
        self.add_user_credentials()
        list_url = reverse('study-list')
        api_data = {'data': {'name': 'study9',
                             'description': 'description9',
                             'active': True},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the study'])
        api_data = {'data': {'name': 'study9',
                             'description': 'description9',
                             'active': True},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['metadata'],
                         {'group': 'userGroup', 'is_public': False})

    def test_user_can_not_change_group(self):
        self.add_user_credentials()
        detail_url = reverse('study-detail', kwargs={'name': 'study4'})
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
        detail_url = reverse('study-detail', kwargs={'name': 'study4'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # public
        detail_url = reverse('study-detail', kwargs={'name': 'study3'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        list_url = reverse('study-list')
        response = self.client.get(list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_bulk_create(self):
        self.add_user_credentials()
        list_url = reverse('study-list')
        api_data = [{'data': {'name': 'study4',
                              'description': 'BGE0006',
                              'active': True},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    {'data': {'name': 'study5', 'description': 'BGE0006',
                              'active': True},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the study',
             'can not set group or is public while creating the study'])

        self.assertEqual(len(self.client.get(list_url).json()), 3)
        # correct data
        api_data = [{'data': {'name': 'study5', 'description': 'BGE0006',
                              'active': True},
                     'metadata': {}},
                    {'data': {'name': 'study6', 'description': 'BGE0006',
                              'active': True},
                     'metadata': {}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 5)

        # Should fail, can not add again same item
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)
        self.assertEqual(len(self.client.get(list_url).json()), 5)


class StudyCsvViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        studies_fpath = join(TEST_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)

    def test_csv(self):
        list_url = reverse('study-list')
        response = self.client.get(list_url, data={'format': 'csv'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content

        a = b'NAME,DESCRIPTION,ACTIVE,START_DATE,END_DATE,LOCATION,CONTACT,PROJECT_NAME\r\n'
        b = b'study1,description1,False,2017-01-17,2017-12-01,Valencia,Alguien,\r\n'
        c = b'study3,description3,True,2017-01-17,2017-12-01,Valencia,Alguien,\r\n'

        for piece in (a, b, c):
            self.assertIn(piece, content)