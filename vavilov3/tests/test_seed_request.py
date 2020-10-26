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
from vavilov3.conf import settings
from vavilov3.mail import prepare_mail_request
from vavilov3.tests.data_io import (load_institutes_from_file,
                                    load_accessions_from_file,
                                    assert_error_is_equal)
from vavilov3.entities.seed_request import (SeedRequestStruct,
                                            create_seed_request_in_db)
from vavilov3.entities.tags import (GERMPLASM_NUMBER, INSTITUTE_CODE,
                                    REQUEST_UID)

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))

DO_TESTS = False


class SeedRequestViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def create_request(self):
        request = SeedRequestStruct()
        request.request_uid = '{}-{:03d}'.format(date.today().strftime('%Y%m%d'), 1)
        request.requester_name = 'userq'
        request.requester_type = 'genbank'
        request.requester_institution = 'HOME'
        request.requester_email = 'user@pepe.es'
        request.requester_address = 'calle'
        request.requester_city = 'ciudad'
        request.requester_region = 'home33'
        request.requester_postal_code = "12345"
        request.requester_country = 'ESP'
        request.request_date = date.today().strftime('%Y/%m/%d')
        request.request_aim = 'asadasd'
        request.request_comments = 'askjdhaksjdha'
        request.requested_accessions = [{INSTITUTE_CODE: 'ESP004',
                                         GERMPLASM_NUMBER: 'BGE0001'}]
        return request

    def test_create_function(self):
        if DO_TESTS:
            request = self.create_request()
            request_db = create_seed_request_in_db(request.get_api_document())[0]
            struct = SeedRequestStruct(instance=request_db)
            expected = request.get_api_document()
            result = struct.get_api_document()
            # del result['data'][REQUEST_UID]
            assert result == expected

    def test_create_by_endpoint(self):
        if DO_TESTS:
            request = self.create_request()
            requests_url = reverse('seedrequest-list')
            response = self.client.post(requests_url, format='json',
                                        data=request.get_api_document())

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            response = self.client.get(requests_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            self.add_admin_credentials()
            # list
            response = self.client.get(requests_url)
            expected = [{
                'data':
                    {
                        'request_uid': '{}-001'.format(date.today().strftime('%Y%m%d')),
                        'name': 'userq', 'type': 'genbank', 'institution': 'HOME',
                        'address': 'calle', 'city': 'ciudad', 'postal_code': '12345',
                        'region': 'home33', 'country': 'ESP', 'email': 'user@pepe.es',
                        'request_date': date.today().strftime('%Y/%m/%d'), 'aim': 'asadasd',
                        'comments': 'askjdhaksjdha',
                        'accessions': [{'instituteCode': 'ESP004', 'germplasmNumber': 'BGE0001'}]},
                'metadata': {}
            }]
            result = response.json()
            self.assertEqual(result, expected)

            request_uid = '{}-001'.format(date.today().strftime('%Y%m%d'))
            # just one
            detail_url = reverse('seedrequest-detail',
                                 kwargs={'request_uid': request_uid})

            response = self.client.get(detail_url)

            request = SeedRequestStruct(response.json())
            result = request.get_api_document()
            self.assertEqual(result, expected[0])
            # update
            detail_url = reverse('seedrequest-detail',
                                 kwargs={'request_uid': request_uid})

            response = self.client.put(detail_url, data={'': ''})
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

            response = self.client.patch(detail_url, data={'': ''})
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

            # delete
            detail_url = reverse('seedrequest-detail',
                                 kwargs={'request_uid': request_uid})

            response = self.client.delete(detail_url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_with_fields(self):
        if DO_TESTS:
            request = self.create_request()
            requests_url = reverse('seedrequest-list')
            response = self.client.post(requests_url, format='json',
                                        data=request.get_api_document())
            self.assertEqual(response.json(),
                             [{'data': {'request_uid': '{}-{:03d}'.format(date.today().strftime('%Y%m%d'), 1),
                                        'name': 'userq',
                                        'type': 'genbank', 'institution': 'HOME',
                                        'address': 'calle', 'city': 'ciudad',
                                        'postal_code': '12345', 'region': 'home33',
                                        'country': 'ESP', 'email': 'user@pepe.es',
                                        'request_date': date.today().strftime('%Y/%m/%d'),
                                        'aim': 'asadasd', 'comments': 'askjdhaksjdha',
                                        'accessions': [{'instituteCode': 'ESP004',
                                                        'germplasmNumber': 'BGE0001'}]},
                              'metadata': {}}])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # fields

            self.add_admin_credentials()
            response = self.client.get(requests_url, data={'fields': 'name'})
            expected = [{'data': {'name': 'userq'},
                         'metadata': {}}]
            self.assertEqual(response.json(), expected)

            # several vields
            response = self.client.get(requests_url, data={'fields': 'name,city,accessions'})
            expected = [{
                'data':
                    {
                        'name': 'userq', 'city': 'ciudad',
                        'accessions': [{'instituteCode': 'ESP004', 'germplasmNumber': 'BGE0001'}]},
                'metadata': {}
            }]
            self.assertEqual(response.json(), expected)

    def test_fail_create_by_endpoint(self):
        if DO_TESTS:
            request = self.create_request()
            request.requested_accessions = [{'instituteCode': 'ESP058', 'germplasmNumber': 'BGE0003'}]
            requests_url = reverse('seedrequest-list')
            response = self.client.post(requests_url, format='json',
                                        data=request.get_api_document())
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert_error_is_equal(response.json(),
                                  ["['This institute has no email to send requests ESP058']"])

    def xtest_create_email(self):
        if DO_TESTS:
            request = self.create_request()
            mail = prepare_mail_request(request)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, settings.SEED_REQUEST_MAIL_SUBJECT)
            self.assertEqual(mail.outbox[0].recipients(), [settings.SEED_REQUEST_MAIL_DEBUG_TO, 'user@pepe.es'])
            self.assertIn("Email de petición de semillas", str(mail.outbox[0].message()))

    def test_check_permissions(self):
        if DO_TESTS:
            request = self.create_request()
            requests_url = reverse('seedrequest-list')
            response = self.client.post(requests_url, format='json',
                                        data=request.get_api_document())
            created_request_uid = response.json()[0]['data'][REQUEST_UID]
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            response = self.client.get(requests_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            detail_url = reverse('seedrequest-detail',
                                 kwargs={'request_uid': created_request_uid})

            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            response = self.client.delete(detail_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            response = self.client.put(detail_url, data={'': ''})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            response = self.client.patch(detail_url, data={'': ''})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
