import os
import tempfile
import hashlib
from os.path import join, abspath, dirname

from django.core.files.base import File

from rest_framework import status
from rest_framework.reverse import reverse

from vavilov3.data_io import initialize_db
from vavilov3.tests import BaseTest
from vavilov3.tests.data_io import (load_accessions_from_file,
                                    load_institutes_from_file,
                                    load_studies_from_file,
                                    load_observation_unit_from_file)
from vavilov3.models import ObservationUnit, ObservationImage
from vavilov3.conf.settings import PHENO_IMAGE_DIR
from vavilov3.entities.tags import INSTITUTE_CODE, GERMPLASM_NUMBER

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))
JSONS_DATA_DIR = join(TEST_DATA_DIR, 'jsons')


class ObservationImageViewTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(JSONS_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(JSONS_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        studies_fpath = join(JSONS_DATA_DIR, 'studies.json')
        load_studies_from_file(studies_fpath)
        fpath = join(JSONS_DATA_DIR, 'observation_units.json')
        load_observation_unit_from_file(fpath)

    def _upload_photos(self):
        obs_units = ObservationUnit.objects.all()
        for index, photo in enumerate(os.listdir(join(TEST_DATA_DIR, 'images'))):
            image_fhand = open(join(TEST_DATA_DIR, 'images', photo), 'rb')
            sha256 = hashlib.sha256(image_fhand.read()).hexdigest()
            image_fhand.seek(0)
            obs_unit = obs_units[0]
            if index > 1:
                obs_unit = obs_units[1]
            if index > 3:
                obs_unit = obs_units[2]
            if index > 5:
                obs_unit = obs_units[3]

            ObservationImage.objects.create(observation_image_uid=sha256,
                                            observation_unit=obs_unit,
                                            image=File(image_fhand))

    def test_model(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.settings(MEDIA_ROOT=tmp_dir):
                photo1 = open(join(TEST_DATA_DIR, 'images', 'photo1.JPG'), mode='rb')
                sha256 = hashlib.sha256(photo1.read()).hexdigest()
                photo1.seek(0)
                obs_unit = ObservationUnit.objects.first()
                obs_image = ObservationImage.objects.create(observation_image_uid=sha256,
                                                            observation_unit=obs_unit,
                                                            image=File(photo1))
                images_dir = join(tmp_dir, PHENO_IMAGE_DIR,
                                  '{}-{}'.format(obs_unit.accession.institute.code,
                                                 obs_unit.accession.germplasm_number),
                                  obs_unit.study.name)

                self.assertEqual(len(os.listdir(images_dir)), 3)

                obs_image.delete()
                self.assertEqual(len(os.listdir(images_dir)), 0)

    def test_read_and_permissions(self):
        list_url = reverse('observationimage-list')
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.settings(MEDIA_ROOT=tmp_dir):
                self._upload_photos()
                obs_unit = ObservationUnit.objects.first()
                images_dir = join(tmp_dir, PHENO_IMAGE_DIR,
                                  '{}-{}'.format(obs_unit.accession.institute.code,
                                                 obs_unit.accession.germplasm_number),
                                  obs_unit.study.name)
                # how many photos ar in the first obs_unit -> 2 photos * small and medium
                self.assertEqual(len(os.listdir(images_dir)), 6)

                # list only public
                response = self.client.get(list_url)
                self.assertEqual(len(response.json()), 4)

                # list only public and users
                self.add_user_credentials()
                response = self.client.get(list_url)
                self.assertEqual(len(response.json()), 6)

                # list all
                self.add_admin_credentials()
                response = self.client.get(list_url)
                self.assertEqual(len(response.json()), 8)

    def test_readonly_with_fields(self):
        list_url = reverse('observationimage-list')
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.settings(MEDIA_ROOT=tmp_dir):
                self._upload_photos()

                response = self.client.get(list_url, data={'fields': 'image'})
                self.assertEqual(list(response.json()[0].keys()), ['image'])

                response = self.client.get(list_url, data={'fields': 'observation_image_uid,image'})
                self.assertEqual(list(response.json()[0].keys()), ['observation_image_uid', 'image'])

                response = self.client.get(list_url, data={'fields': 'accession,study,image'})
                self.assertSetEqual(set(response.json()[0].keys()),
                                    set(['accession', 'study', 'image']))

    def test_create_delete(self):
        list_url = reverse('observationimage-list')
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.settings(MEDIA_ROOT=tmp_dir):
                content_type = 'multipart'
                photo1_fhand = open(join(TEST_DATA_DIR, 'images', 'photo1.JPG'),
                                    mode='rb')

                self.add_admin_credentials()

                response = self.client.post(list_url,
                                            data={'image': photo1_fhand,
                                                  'study': 'study1',
                                                  INSTITUTE_CODE: 'ESP004',
                                                  GERMPLASM_NUMBER: 'BGE0001'},
                                            format=content_type)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                expected = {'observation_image_uid': '4790dde29556601a330df6b17784da5aab389cc8fb590739f466263ef797b9d0',
                            'observation_unit': '048e8ff1-067f-43f0-b99f-98c2be948b6e',
                            'image': 'tmp/tmp841j5omn/phenotype_images/ESP004-BGE0001/study1/study1_ESP004-BGE0001_4790dde29556601a330df6b17784da5aab389cc8fb590739f466263ef797b9d0.JPG',
                            'image_medium': 'tmp/tmp841j5omn/phenotype_images/ESP004-BGE0001/study1/medium_study1_ESP004-BGE0001_4790dde29556601a330df6b17784da5aab389cc8fb590739f466263ef797b9d0.jpg',
                            'image_small': 'tmp/tmp841j5omn/phenotype_images/ESP004-BGE0001/study1/small_study1_ESP004-BGE0001_4790dde29556601a330df6b17784da5aab389cc8fb590739f466263ef797b9d0.jpg',
                            'study': 'study1', 'accession': {'instituteCode': 'ESP004', 'germplasmNumber': 'BGE0001'}}
                self.assertSetEqual(set(response.json().keys()), set(expected.keys()))

                images_dir = join(tmp_dir, PHENO_IMAGE_DIR,
                                  '{}-{}'.format('ESP004', 'BGE0001'), 'study1')
                self.assertEqual(len(os.listdir(images_dir)), 3)
                return
                detail_url = reverse('observationimage-detail',
                                     kwargs={'observation_image_uid': '4790dde29556601a330df6b17784da5aab389cc8fb590739f466263ef797b9d0'})

                response = self.client.delete(detail_url)
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

                self.assertEqual(len(os.listdir(images_dir)), 0)
