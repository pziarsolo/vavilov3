from collections import OrderedDict
from os.path import join, abspath, dirname

from rest_framework.reverse import reverse
from rest_framework import status

from vavilov3.data_io import initialize_db
from vavilov3.views import DETAIL
from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_studies_from_file,
                                    assert_error_is_equal,
                                    load_accessionsets_from_file,
                                    load_observation_unit_from_file,
                                    load_accessions_from_file,
                                    load_institutes_from_file,
                                    load_observation_variables_from_file,
                                    load_observations_from_file,
                                    load_plants_from_file)
from vavilov3.entities.accession import AccessionStruct
from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER
TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class InstituteViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(fpath)

    def test_bulk_create(self):
        fpath = join(TEST_DATA_DIR, 'institutes_extra.csv')
        bulk_url = reverse('institute-bulk')
        list_url = reverse('institute-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        self.add_admin_credentials()
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 7)

        # adding again fails with error
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 3)

        # adding again fails with error
        fpath = join(TEST_DATA_DIR, 'institutes_extra_with_one_repeated.csv')
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 1)
        self.assertEqual(len(self.client.get(list_url).json()), 7)


class AccessionBulkViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('accession-list')
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession',
             'can not set group or is public while creating the accession'])
        # correct data
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'germplasmNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')

        assert_error_is_equal(response.json(), ['Successfully added 2 items'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 6)

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

        self.assertEqual(len(self.client.get(list_url).json()), 6)

    def test_bulk_create_csv(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'accessions.csv')
        list_url = reverse('accession-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 4)
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath),
                                          'data_source_code': 'CRF',
                                          'data_source_kind': 'project'},
                                    format=content_type)
#         data_source = response.json()[0]['data']['passports'][0][DATA_SOURCE]
#         self.assertEqual(data_source['code'], 'CRF')
#         self.assertEqual(data_source['kind'], 'project')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 10)
#
#         result = response.json()[0]
#         self.assertEqual(result['data']['instituteCode'], 'ESP004')
#         self.assertEqual(result['data']['germplasmNumber'], 'BGE005836')
#         self.assertEqual(result['data']['is_available'], False)
#         self.assertEqual(result['data']['conservation_status'], 'is_active')

        detail_url = reverse('accession-detail',
                             kwargs={'institute_code': 'ESP004',
                                     'germplasm_number': 'BGE005836'})
        response = self.client.get(detail_url)
        accession = AccessionStruct(response.json())
        del accession.passports[0].data['dataSource']['retrievalDate']
        passport = {'version': '1.0',
                    'taxonomy': {'genus': {'name': 'Zea'},
                                 'species': {'name': 'mays', 'author': 'L.'},
                                 'subspecies': {'name': 'mays'}},
                    'otherNumbers': [{'instituteCode': 'ESP058',
                                      'germplasmNumber': 'CIAM81001'}],
                    'germplasmName': 'Millo do pais',
                    'collectionDate': '19811031',
                    'collectionSite': OrderedDict([('countryOfOriginCode', 'ESP'),
                                                   ('state', 'Galicia'),
                                                   ('province', 'La Coruña'),
                                                   ('municipality', 'Fisterra'),
                                                   ('site', 'Duio,San Martiño'),
                                                   ('latitude', 42.925),
                                                   ('longitude', -9.275),
                                                   ('altitude', 101),
                                                   ('coordUncertainty', '1840')]),
                    'commonCropName': 'Maiz',
                    'germplasmNumber': {'instituteCode': 'ESP004',
                                        'germplasmNumber': 'BGE005836'},
                    'collectionNumber': {'instituteCode': 'ESP058',
                                         'fieldCollectionNumber': '81001'},
                    'collectionSource': '20',
                    'dataSource': {'code': 'CRF', 'kind': 'project'},
                    'biologicalStatusOfAccessionCode': '300'}
        self.assertEqual(accession.passports[0].data, passport)
        # adding again fails with error
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath),
                                          'data_source_code': 'CRF',
                                          'data_source_kind': 'passport_collector'},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 6)


class AccessionSetViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        accessionsets_fpath = join(TEST_DATA_DIR, 'accessionsets.json')
        load_accessionsets_from_file(accessionsets_fpath)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('accessionset-list')
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0006'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    {'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0007'},
                     'metadata': {'group': 'userGroup', 'is_public': True}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group or is public while creating the accession',
             'can not set group or is public while creating the accession'])
        # correct data
        self.assertEqual(len(self.client.get(list_url).json()), 2)
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        # Should fail, can not add again same item
        api_data = [{'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0006'},
                     'metadata': {}},
                    {'data': {'instituteCode': 'ESP004',
                              'accessionsetNumber': 'BGE0007'},
                     'metadata': {}}]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)

        self.assertEqual(len(self.client.get(list_url).json()), 4)

    def test_bulk_create_csv(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'accessionsets_extra.csv')
        list_url = reverse('accessionset-list')
        bulk_url = reverse('accessionset-bulk')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 2)
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        # adding again fails with error
        response = self.client.post(bulk_url,
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)


class StudyBulkTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        studies_fpath = join(TEST_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)

    def test_bulk_create_admin(self):
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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

    def test_bulk_create_csv_admin(self):
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

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('observationunit-list')
        self.assertEqual(len(self.client.get(list_url).json()), 4)

        api_data = [
            {'data': {
                "name": "Plant 5",
                "accession": {
                    "instituteCode": "ESP004",
                    "germplasmNumber": "BGE0001"
                },
                "level": "plant",
                "replicate": "0",
                "study": "study2"},
             'metadata': {'group': 'admin'}},
            {'data': {
                "name": "Plant 6",
                "accession": {
                    "instituteCode": "ESP004",
                    "germplasmNumber": "BGE0001"
                },
                "level": "plant",
                "replicate": "0",
                "study": "study2"},
             'metadata': {'group': 'admin'}}
        ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group while creating the observation unit',
             'can not set group while creating the observation unit'])
        # correct data
        api_data = [{'data': {"name": "Plant 5",
                              "accession": {
                                  "instituteCode": "ESP004",
                                  "germplasmNumber": "BGE0001"
                              },
                              "level": "plant",
                              "replicate": "0",
                              "study": "study2"},
                     'metadata': {}},
                    {'data': {"name": "Plant 6",
                              "accession": {
                                  "instituteCode": "ESP004",
                                  "germplasmNumber": "BGE0001"
                              },
                              "level": "plant",
                              "replicate": "0",
                              "study": "study2"},
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
        fpath = join(TEST_DATA_DIR, 'observation_units.csv')
        list_url = reverse('observationunit-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 4)
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 8)
        result = response.json()[0]
        self.assertEqual(result['data']['name'], 'Plant 7')
        self.assertEqual(result['data']['accession'], {INSTITUTE_CODE: 'ESP004',
                                                       GERMPLASM_NUMBER: 'BGE0001'})
        self.assertEqual(result['data']['level'], 'Plant')
        self.assertEqual(result['data']['replicate'], '0')
        self.assertEqual(result['data']['study'], 'study1')

        detail_url = reverse('observationunit-detail',
                             kwargs={'name': 'Plant 7'})
        response = self.client.get(detail_url)

        self.assertEqual(response.json(),
                         {'data': {"name": "Plant 7",
                                   "accession": {
                                       "instituteCode": "ESP004",
                                       "germplasmNumber": "BGE0001"
                                   },
                                   "level": "Plant",
                                   "replicate": "0",
                                   "study": "study1"},
                          'metadata': {'group': 'admin'}})

        # adding again fails with error
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 4)


class ObservationVariableViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        fpath = join(TEST_DATA_DIR, 'observation_variables.json')
        load_observation_variables_from_file(fpath)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('observationvariable-list')
        api_data = [{'data': {'name': 'Plant size:cm1',
                              'trait': 'Plant sizeee',
                              'description': 'Measure of plant heigth',
                              'method': 'by tape', 'data_type': 'Numerical',
                              'unit': 'centimeter'},
                     'metadata': {'group': 'userGroup'}},
                    {'data': {'name': 'Plant size:cm2',
                              'trait': 'Plant sizeee',
                              'description': 'Measure of plant heigth',
                              'method': 'by tape', 'data_type': 'Numerical',
                              'unit': 'centimeter'},
                     'metadata': {'group': 'admin'}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group while creating the observation variable',
             'can not set group while creating the observation variable'])
        # correct data
        api_data = [{'data': {'name': 'Plant size:cm1',
                              'trait': 'Plant sizeee',
                              'description': 'Measure of plant heigth',
                              'method': 'by tape', 'data_type': 'Numerical',
                              'unit': 'centimeter'},
                     'metadata': {}},
                    {'data': {'name': 'Plant size:cm2',
                              'trait': 'Plant sizeee',
                              'description': 'Measure of plant heigth',
                              'method': 'by tape', 'data_type': 'Numerical',
                              'unit': 'centimeter'},
                     'metadata': {}},
                    ]

        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 5)

        # Should fail, can not add again same item
        api_data = [{'data': {'name': 'Plant size:cm1',
                              'trait': 'Plant sizeee',
                              'description': 'Measure of plant heigth',
                              'method': 'by tape', 'data_type': 'Numerical',
                              'unit': 'centimeter'},
                     'metadata': {}},
                    {'data': {'name': 'Plant size:cm2',
                              'trait': 'Plant sizeee',
                              'description': 'Measure of plant heigth',
                              'method': 'by tape', 'data_type': 'Numerical',
                              'unit': 'centimeter'},
                     'metadata': {}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)

        self.assertEqual(len(self.client.get(list_url).json()), 5)

    def test_bulk_create_csv(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'observation_variables.csv')
        list_url = reverse('observationvariable-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 3)
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 6)
        result = response.json()[0]
        self.assertEqual(result['data']['name'], 'color:colorimeter')
        self.assertEqual(result['data']['description'], 'trait2 desc')
        self.assertEqual(result['data']['trait'], 'color')
        self.assertEqual(result['data']['method'], 'colorimeter')
        self.assertEqual(result['data']['data_type'], 'Nominal')

        detail_url = reverse('observationvariable-detail',
                             kwargs={'name': 'color:colorimeter'})
        response = self.client.get(detail_url)

        self.assertEqual(response.json(),
                         {'data': {'name': 'color:colorimeter',
                                   'description': 'trait2 desc',
                                   'trait': 'color',
                                   'method': 'colorimeter',
                                   'data_type': 'Nominal'},
                          'metadata': {'group': 'admin'}})

        # adding again fails with error
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 3)


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
        fpath = join(TEST_DATA_DIR, 'observation_variables.json')
        load_observation_variables_from_file(fpath)

        fpath = join(TEST_DATA_DIR, 'observations.json')
        load_observations_from_file(fpath, obs_group='OBS1', user=self.crf_user)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('observation-list')
        self.assertEqual(len(self.client.get(list_url).json()), 3)

        api_data = [
            {
                'observation_variable': 'Plant size:cm',
                'observation_unit': 'Plant 2',
                'value': '12',
                'observer': 'observer1',
                'creation_time': '1911-12-03 00:23:00',
            },
            {
                'observation_variable': 'Plant size:cm',
                'observation_unit': 'Plant 2',
                'value': '1',
                'observer': 'observer1',
                'creation_time': '1911-12-03 00:23:00',
            },

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

    def test_bulk_create_csv(self):
        self.add_admin_credentials()
        fpath = join(TEST_DATA_DIR, 'observation.csv')
        list_url = reverse('observation-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 3)
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 6)

        result = response.json()[0]
        self.assertEqual(result['observation_variable'], 'Plant size:cm')
        self.assertEqual(result['observation_unit'], 'Plant 2')
        self.assertEqual(result['creation_time'], '1911-12-03 00:23:00')
        self.assertEqual(result['observer'], 'me')
        self.assertEqual(result['value'], '12')

        detail_url = reverse('observation-detail',
                             kwargs={'observation_id': result['observation_id']})
        response = self.client.get(detail_url)
        self.assertEqual(response.json(),
                         {'observation_id': result['observation_id'],
                          'observation_variable': 'Plant size:cm',
                          'observation_unit': 'Plant 2',
                          'value': '12', 'observer': 'me',
                          'creation_time': '1911-12-03 06:23:00',
                          'study': 'study2',
                          'accession': {
                              'instituteCode': 'ESP026',
                              'germplasmNumber': 'BGE0002'}})

        # adding again fails with error
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 3)


class PlantViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        fpath = join(TEST_DATA_DIR, 'plants.json')
        load_plants_from_file(fpath)

    def test_bulk_create(self):
        self.add_admin_credentials()
        list_url = reverse('plant-list')
        api_data = [{'data': {'name': 'Plant 5'
                              },
                     'metadata': {'group': 'userGroup'}},
                    {'data': {'name': 'Plant 6'
                              },
                     'metadata': {'group': 'admin'}},
                    ]
        response = self.client.post(list_url + 'bulk/', data=api_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert_error_is_equal(
            response.json(),
            ['can not set group while creating the plant',
             'can not set group while creating the plant'])
        # correct data
        api_data = [
            {'data': {'name': 'Plant 5'},
             'metadata': {}},
            {'data': {'name': 'Plant 6'},
             'metadata': {}}]

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
        fpath = join(TEST_DATA_DIR, 'plants.csv')
        list_url = reverse('plant-list')
        content_type = 'multipart'
        self.assertEqual(len(self.client.get(list_url).json()), 4)
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(list_url).json()), 6)
        result = response.json()[0]
        self.assertEqual(result['data']['name'], 'Plant 7')
        self.assertEqual(result['data']['x'], '1')
        self.assertEqual(result['data']['y'], '1')
        self.assertEqual(result['data']['plant_number'], '6')
        self.assertEqual(result['data']['entry_number'], '6')

        detail_url = reverse('plant-detail',
                             kwargs={'name': 'Plant 7'})
        response = self.client.get(detail_url)

        self.assertEqual(response.json(),
                         {'data': {'name': 'Plant 7',
                                   'x': '1',
                                   'y': '1',
                                   'plant_number': '6',
                                   'entry_number': '6'},
                          'metadata': {'group': 'admin'}})

        # adding again fails with error
        response = self.client.post(list_url + 'bulk/',
                                    data={'csv': open(fpath)},
                                    format=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.json()[DETAIL]), 2)
