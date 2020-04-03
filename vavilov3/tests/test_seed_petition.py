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
from datetime import date

from django.core import mail

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.tests import BaseTest
from vavilov3.data_io import initialize_db
from vavilov3.tests.data_io import (load_institutes_from_file,
                                    load_accessions_from_file,
                                    assert_error_is_equal)
from vavilov3.entities.seed_petition import (SeedPetitionStruct,
                                             create_seed_petition_in_db)
from vavilov3.entities.tags import (GERMPLASM_NUMBER, INSTITUTE_CODE,
                                    PETITION_ID)
from vavilov3.conf import settings
from vavilov3.mail import prepare_and_send_seed_petition_mails

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


class SeedPetitionViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def create_petition(self):
        petition = SeedPetitionStruct()
        petition.petitioner_name = 'userq'
        petition.petitioner_type = 'genbank'
        petition.petitioner_institution = 'HOME'
        petition.petitioner_email = 'user@pepe.es'
        petition.petitioner_address = 'calle'
        petition.petitioner_city = 'ciudad'
        petition.petitioner_region = 'home33'
        petition.petitioner_postal_code = "12345"
        petition.petitioner_country = 'ESP'
        petition.petition_date = date.today().strftime('%Y/%m/%d')
        petition.petition_aim = 'asadasd'
        petition.petition_comments = 'askjdhaksjdha'
        petition.petition_accessions = [{INSTITUTE_CODE: 'ESP004',
                                         GERMPLASM_NUMBER: 'BGE0001'}]
        return petition

    def test_create_function(self):
        petition = self.create_petition()
        petition_db = create_seed_petition_in_db(petition.get_api_document())[0]
        struct = SeedPetitionStruct(instance=petition_db)
        expected = petition.get_api_document()
        result = struct.get_api_document()
        del result['data'][PETITION_ID]
        assert result == expected

    def test_create_by_endpoint(self):
        petition = self.create_petition()
        petitions_url = reverse('seedpetition-list')
        response = self.client.post(petitions_url, format='json',
                                    data=petition.get_api_document())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(petitions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.add_admin_credentials()
        # list
        response = self.client.get(petitions_url)
        expected = [{
            'data':
                {
                    'name': 'userq', 'type': 'genbank', 'institution': 'HOME',
                    'address': 'calle', 'city': 'ciudad', 'postal_code': '12345',
                    'region': 'home33', 'country': 'ESP', 'email': 'user@pepe.es',
                    'petition_date': date.today().strftime('%Y/%m/%d'), 'aim': 'asadasd',
                    'comments': 'askjdhaksjdha',
                    'accessions': [{'instituteCode': 'ESP004', 'germplasmNumber': 'BGE0001'}]},
            'metadata': {}
        }]
        result = response.json()
        del result[0]['data']['petition_id']
        self.assertEqual(response.json(), expected)
        # just one
        detail_url = reverse('seedpetition-detail', kwargs={'pk': 2})

        response = self.client.get(detail_url)

        petition = SeedPetitionStruct(response.json())
        result = petition.get_api_document()
        del result['data']['petition_id']
        self.assertEqual(result, expected[0])
        # update
        detail_url = reverse('seedpetition-detail', kwargs={'pk': 2})

        response = self.client.put(detail_url, data={'': ''})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.patch(detail_url, data={'': ''})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # delete
        detail_url = reverse('seedpetition-detail', kwargs={'pk': 2})

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_with_fields(self):
        petition = self.create_petition()
        petitions_url = reverse('seedpetition-list')
        response = self.client.post(petitions_url, format='json',
                                    data=petition.get_api_document())
        self.assertEqual(response.json(),
                         [{'data': {'petition_id': 5, 'name': 'userq',
                                    'type': 'genbank', 'institution': 'HOME',
                                    'address': 'calle', 'city': 'ciudad',
                                    'postal_code': '12345', 'region': 'home33',
                                    'country': 'ESP', 'email': 'user@pepe.es',
                                    'petition_date': date.today().strftime('%Y/%m/%d'),
                                    'aim': 'asadasd', 'comments': 'askjdhaksjdha',
                                    'accessions': [{'instituteCode': 'ESP004',
                                                    'germplasmNumber': 'BGE0001'}]},
                          'metadata': {}}])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # fields

        self.add_admin_credentials()
        response = self.client.get(petitions_url, data={'fields': 'name'})
        expected = [{'data': {'name': 'userq'},
                     'metadata': {}}]
        self.assertEqual(response.json(), expected)

        # several vields
        response = self.client.get(petitions_url, data={'fields': 'name,city,accessions'})
        expected = [{
            'data':
                {
                    'name': 'userq', 'city': 'ciudad',
                    'accessions': [{'instituteCode': 'ESP004', 'germplasmNumber': 'BGE0001'}]},
            'metadata': {}
        }]
        self.assertEqual(response.json(), expected)

    def test_fail_create_by_endpoint(self):
        petition = self.create_petition()
        petition.petition_accessions = [{'instituteCode': 'ESP058', 'germplasmNumber': 'BGE0003'}]
        petitions_url = reverse('seedpetition-list')
        response = self.client.post(petitions_url, format='json',
                                    data=petition.get_api_document())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(response.json(),
                              ["['This institute has no email to send petitions ESP058']"])

    def test_create_email(self):
        petition = self.create_petition()
        prepare_and_send_seed_petition_mails(petition)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, settings.SEED_PETITION_MAIL_SUBJECT)
        self.assertEqual(mail.outbox[0].recipients(), [settings.SEED_PETITION_MAIL_DEBUG_TO, 'user@pepe.es'])
        self.assertIn("Email de petición de semillas", str(mail.outbox[0].message()))

    def test_check_permissions(self):
        petition = self.create_petition()
        petitions_url = reverse('seedpetition-list')
        response = self.client.post(petitions_url, format='json',
                                    data=petition.get_api_document())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(petitions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        detail_url = reverse('seedpetition-detail', kwargs={'pk': 1})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(detail_url, data={'': ''})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch(detail_url, data={'': ''})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

