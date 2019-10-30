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

from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import assert_error_is_equal, load_traits_from_file, \
    load_traits_from_obo_file
from vavilov3.data_io import initialize_db
from vavilov3.entities.trait import parse_obo, transform_to_trait_entity_format

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


class TraitViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()

        trait_fpath = join(TEST_DATA_DIR, 'traits.json')
        load_traits_from_file(trait_fpath)

    def test_read_only(self):
        list_url = reverse('trait-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 2)

        expected = [
            {"name": "Plant size", "description": "Plant size",
             'ontology': None, 'ontology_id': None},
            {"name": "Plant Growth type",
             "description": "Plant Growth type",
             'ontology': None, 'ontology_id': None}]
        self.assertEqual(result, expected)

    def test_readonly_with_fields(self):
        detail_url = reverse('trait-detail', kwargs={'name': 'Plant size'})
        response = self.client.get(detail_url, data={'fields': 'name'})

        self.assertEqual(response.json(), {'name': 'Plant size'})

        response = self.client.get(detail_url, data={'fields': 'name,description'})
        self.assertEqual(response.json(), {'name': 'Plant size',
                                           'description': "Plant size"})

    def test_create_delete(self):
        self.add_admin_credentials()
        list_url = reverse('trait-list')
        api_data = {
            "name": "fruit color",
            "description": "fruit color",
        }

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # bad data
        bad_api_data = {
            "description": "milimeter"}
        response = self.client.post(list_url, data=bad_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['name mandatory'])

        # adding agian should fail
        with transaction.atomic():
            response = self.client.post(list_url, data=api_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        detail_url = reverse('trait-detail',
                             kwargs={"name": "fruit color"})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('trait-detail',
                             kwargs={'name': 'Plant size'})

        api_data = {
            'name': 'Plant size', 'description': 'centimeter',
            'ontology': None, 'ontology_id': None
        }

        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        response = self.client.get(detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

    def test_filter(self):
        self.add_admin_credentials()
        list_url = reverse('trait-list')
        response = self.client.get(list_url,
                                   data={'name': 'Plant size'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(list_url,
                                   data={'name__icontains': 'plant'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_permissions(self):
        self.add_user_credentials()
        detail_url = reverse('trait-detail', kwargs={'name': 'Plant size'})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        list_url = reverse('trait-list')
        response = self.client.post(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonym_permissions(self):
        detail_url = reverse('trait-detail', kwargs={'name': 'Plant size'})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(detail_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        list_url = reverse('trait-list')
        response = self.client.post(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_create_by_obo(self):
#         self.add_admin_credentials()
#         obo_fpath = join(TEST_DATA_DIR, 'to.obo')
#         create_obo_url = reverse('trait-create-by-obo')
#         response = self.client.post(create_obo_url,
#                                     data={'obo': open(obo_fpath)})
#         print(response.json())


class TraitOboViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()

    def test_obo_serializer(self):
        obo_fpath = join(TEST_DATA_DIR, '..', 'to.obo')
        ontology = parse_obo(open(obo_fpath))
        traits = transform_to_trait_entity_format(ontology)
        assert len(traits) == 1528

    def test_load_to(self):
        obo_fpath = join(TEST_DATA_DIR, '..', 'to.obo')
        load_traits_from_obo_file(obo_fpath)
