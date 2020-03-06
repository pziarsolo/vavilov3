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

from vavilov3.entities.tags import (DATA_SOURCE, GERMPLASM_NUMBER, CONSTATUS,
                                    IS_AVAILABLE, PASSPORTS,
    IN_NUCLEAR_COLLECTION)
from vavilov3.passport.tags import (BIO_STATUS,
                                    INSTITUTE_CODE, REMARKS,
                                    MLSSTATUS, COLLECTION_SOURCE,
                                    RETRIEVAL_DATE, COUNTRY, PROVINCE,
                                    COLLECTION_SITE, SITE, LATITUDE, ALTITUDE,
                                    LONGITUDE, COORDUNCERTAINTY, COLLECTION_NUMBER,
                                    FIELD_COLLECTION_NUMBER, COLLECTION_DATE, OTHER_NUMBERS)

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
        self.assertEqual(result['data'][INSTITUTE_CODE], 'ESP004')
        self.assertEqual(result['data'][GERMPLASM_NUMBER], 'BGE0001')
        self.assertEqual(result['data'][IS_AVAILABLE], True)
        self.assertEqual(result['data'][CONSTATUS], 'is_active')
        self.assertTrue(result['data'][PASSPORTS])
        self.assertEqual(result['data'][PASSPORTS][0][DATA_SOURCE],
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
                                   data={'fields': INSTITUTE_CODE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data'][INSTITUTE_CODE], 'ESP004')
        self.assertEqual(len(response.json()['data'].keys()), 1)

        response = self.client.get(
            detail_url,
            data={'fields': 'instituteCode,passports,genera'})
        self.assertEqual(response.json()['data'][INSTITUTE_CODE], 'ESP004')
        self.assertEqual(len(response.json()['data'][PASSPORTS]), 1)
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
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
                             GERMPLASM_NUMBER: 'BGE0005'},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession'])
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
                             GERMPLASM_NUMBER: 'BGE0005'},
                    'metadata': {}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json()['data'], api_data['data'])

        # bad payload data
        api_data = {'data': {INSTITUTE_CODE: 'ESP004'},
                    'metadata': {'group': 'admin', 'is_public': True}}
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(), ['germplasmNumber mandatory'])

        with transaction.atomic():
            api_data = {'data': {INSTITUTE_CODE: 'ESP004',
                                 GERMPLASM_NUMBER: 'BGE0005'},
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

        # full info accession creation

        api_data = {
            "metadata": {},
            "data": {
                INSTITUTE_CODE: "ESP004",
                IS_AVAILABLE: False,
                CONSTATUS: "is_active",
                GERMPLASM_NUMBER: "LO6032",
                IN_NUCLEAR_COLLECTION: True,
                PASSPORTS: [
                    {
                        GERMPLASM_NUMBER: {
                            INSTITUTE_CODE: "ESP026",
                            GERMPLASM_NUMBER: "LO6032"
                        },
                        COLLECTION_SOURCE: "13",
                        "version": "1.0",
                        BIO_STATUS: "100",
                        "mlsStatus": "N",
                        "taxonomy": {
                            "species": {
                                "name": "resupinatum",
                                "author": "L."
                            },
                            "genus": {
                                "name": "Trifolium"
                            }
                        },
                        "dataSource": {
                            RETRIEVAL_DATE: "2019-05-30",
                            "kind": "project",
                            "code": "CRF"
                        },
                        COLLECTION_SITE: {
                            COUNTRY: "PRT",
                            PROVINCE: "Beja",
                            SITE: "Moura_Safara cruce Amareleja al lado de una carbonera",
                            LATITUDE: 38.125,
                            LONGITUDE:-7.24166666666667,
                            ALTITUDE: 131,
                            COORDUNCERTAINTY: "1840"
                        },
                        COLLECTION_NUMBER: {
                            INSTITUTE_CODE: "ESP026",
                            FIELD_COLLECTION_NUMBER: "ESPO-Tr28"
                        },
                        COLLECTION_DATE: "19980709",
                        OTHER_NUMBERS: [
                            {
                                INSTITUTE_CODE: "ESP026",
                                GERMPLASM_NUMBER: "BGE033362"
                            }
                        ]
                    }
                ]
            }
        }
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["data"], api_data["data"])
        self.assertEqual(response.json()["metadata"], {'group': 'admin', 'is_public': False})

        api_data["data"][GERMPLASM_NUMBER] = "LO6033"
        api_data["data"][IN_NUCLEAR_COLLECTION] = True
        api_data["data"]["passports"][0][GERMPLASM_NUMBER][GERMPLASM_NUMBER] = "LO6033"

        # passports need an accession number
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0].pop(GERMPLASM_NUMBER)
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # taxonomy can be empty
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0].pop("taxonomy")
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        detail_url = reverse("accession-detail", kwargs={'institute_code': 'ESP004',
                                                         'germplasm_number': "LO6033"})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # taxonomy can't have undefined fields
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0]["taxonomy"] = {"category": {"name": "puntiagudo",
                                                                         "author": "admin"}}
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # datasource can be empty
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0].pop("dataSource")
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # datasource can have only id
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0]["dataSource"]["padrino"] = "Fernando"
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # retrievaldate should be a valid date
        response = self.client.delete(detail_url)
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0]["dataSource"][RETRIEVAL_DATE] = "lunes"
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Datasource should have kind and code
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0]["dataSource"] = {RETRIEVAL_DATE: "2019-05-30"}
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Origin country should be 3 characters long
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][COLLECTION_SITE][COUNTRY] = "PORTUGAL"
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Latitude should be a number
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][COLLECTION_SITE][LATITUDE] = "Arriba"
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Altitude should be a number
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][COLLECTION_SITE][ALTITUDE] = "Abajo"
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # longitude should be a number
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][COLLECTION_SITE][LONGITUDE] = "Alolargo"
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Collection site shouldn't have unespecified fields
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][COLLECTION_SITE]["esquina"] = "La que da sombra"
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Bio status value should be defined in the biostatus codes
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][BIO_STATUS] = '100'
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][BIO_STATUS] = '666'
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # remarks should have the correct fields
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][REMARKS] = {'collection': 'notes of the collection',
                                                         'genebank_management': 'aaa'}
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][REMARKS] = {'notes': 'notes of the collection',
                                                         'database': 'aaa'}
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # MLSSTATUS can only be 'Y' or 'N'
        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][MLSSTATUS] = 'Y'
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        new_api_data = deepcopy(api_data)
        new_api_data["data"]["passports"][0][MLSSTATUS] = 'yes'
        response = self.client.post(list_url, data=new_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # users can create accessions
        self.remove_credentials()
        self.add_user_credentials()
        user_api_data = {
            "metadata": {},
            "data": {
                INSTITUTE_CODE: "ESP004",
                "is_available": False,
                "conservation_status": "is_active",
                GERMPLASM_NUMBER: "LO666"}
        }
        response = self.client.post(list_url, data=user_api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update(self):
        self.add_admin_credentials()
        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0001'})
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
                             'germplasmNumber': 'BGE0001'},
                    'metadata': {'group': 'admin', 'is_public': False}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # admin can change group
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
                             'germplasmNumber': 'BGE0001'},
                    'metadata': {'group': 'userGroup', 'is_public': True}}
        response = self.client.put(detail_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), api_data)

        # Fail changing group if not exists
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
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
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
                             'germplasmNumber': 'BGE0005'},
                    'metadata': {'group': 'admin', 'is_public': True}}

        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession'])
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
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

    def test_user_cannot_make_public(self):
        self.add_user_credentials()
        list_url = reverse('accession-list')
        api_data = {'data': {INSTITUTE_CODE: 'ESP004',
                             'germplasmNumber': 'BGE0005'},
                    'metadata': {}}
        response = self.client.post(list_url, data=api_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['metadata'],
                         {'group': 'userGroup', 'is_public': False})

        detail_url = reverse("accession-detail",
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE0005'})

        public_api_data = deepcopy(api_data)
        public_api_data["metadata"] = {'group': 'userGroup', 'is_public': True}
        response = self.client.put(detail_url, data=public_api_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    """ def test_bulk_create_with_errors(self):
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

        self.assertEqual(len(self.client.get(list_url).json()), 5) """


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
