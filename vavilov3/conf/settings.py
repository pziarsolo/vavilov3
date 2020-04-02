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
from os.path import abspath, join, dirname
from django.conf import settings

TEMPLATE_DIR = abspath(join(dirname(__file__), '..', 'templates'))

ADMIN_GROUP = getattr(settings, 'VAVILOV3_ADMIN_GROUP', 'admin')

ALLOWED_TAXONOMIC_RANKS = ['family', 'genus', 'species', 'subspecies',
                           'variety', 'convarietas', 'group', 'forma']
USERS_CAN_CREATE_ACCESSIONSETS = getattr(
    settings, 'VAVILOV3_USERS_CAN_CREATE_ACCESSIONSETS', False)

DEF_ACCESSION_CSV_FIELDS = [
    'PUID', 'INSTCODE', 'ACCENUMB', 'CONSTATUS', 'IS_AVAILABLE',
    'IN_NUCLEAR_COLLECTION', 'COLLNUMB',
    'COLLCODE', 'GENUS', 'SPECIES', 'SPAUTHOR', 'SUBTAXA', 'SUBTAUTHOR',
    'CROPNAME', 'ACCENAME', 'ACQDATE', 'ORIGCTY', 'COLLSITE',
    'LATITUDE', 'LONGITUDE', 'COORDUNCERT', 'COORDDATUM',
    'GEOREFMETH', 'ELEVATION', 'COLLDATE', 'BREDCODE',
    'SAMPSTAT', 'ANCEST', 'COLLSRC', 'DONORCODE', 'DONORNUMB',
    'OTHERNUMB', 'DUPLSITE', 'STORAGE', 'MLSSTAT', 'REMARKS']
ACCESSION_CSV_FIELDS = getattr(settings, 'VAVILOV3_ACCESSION_CSV_FIELDS',
                               DEF_ACCESSION_CSV_FIELDS)

DEF_ACCESSIONSET_CSV_FIELDS = ['INSTCODE', 'ACCESETNUMB', 'ACCESSIONS']
ACCESSIONSET_CSV_FIELDS = getattr(settings, 'VAVILOV3_ACCESSIONSET_CSV_FIELDS',
                                  DEF_ACCESSIONSET_CSV_FIELDS)
DEF_INSTITUTE_CSV_FIELDS = ['INSTCODE', 'FULL_NAME', 'TYPE', 'STREET_POB',
                            'CITY_STATE', 'ZIP_CODE', 'PHONE', 'EMAIL',
                            'URL', 'MANAGER']
INSTITUTE_CSV_FIELDS = getattr(settings, 'VAVILOV3_INSTITUTE_CSV_FIELDS',
                               DEF_INSTITUTE_CSV_FIELDS)

DEF_STUDY_CSV_FIELDS = ['NAME', 'DESCRIPTION', 'START_DATE',
                        'END_DATE', 'LOCATION', 'CONTACT', 'PROJECT_NAME']
STUDY_CSV_FIELDS = getattr(settings, 'VAVILOV3_STUDY_CSV_FIELDS',
                           DEF_STUDY_CSV_FIELDS)

DEF_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT = getattr(settings, 'VAVILOV3_DATETIME_FORMAT',
                          DEF_DATETIME_FORMAT)

DEF_OBSERVATION_CSV_FIELDS = ['OBSERVATION_ID', 'STUDY', 'ACCESSION',
                              'OBSERVATION_VARIABLE', 'OBSERVATION_UNIT',
                              'VALUE', 'CREATION_TIME', 'OBSERVER']
OBSERVATION_CSV_FIELDS = getattr(settings, 'VAVILOV3_OBSERVATION_CSV_FIELDS',
                                 DEF_OBSERVATION_CSV_FIELDS)

PHENO_IMAGE_DIR = getattr(settings, 'VAVILOV3_PHENO_IMAGE_DIR',
                          'phenotype_images')

LONG_PROCESS_TIMEOUT = getattr(settings, 'VAVILOV3_LONG_PROCESS_TIMEOUT',
                               14400)
SHORT_PROCESS_TIMEOUT = getattr(settings, 'VAVILOV3_LONG_PROCESS_TIMEOUT',
                                1800)

#  this directory must be writable by web server and celery
TMP_DIR = getattr(settings, 'VAVILOV3_TMP_DIR', None)

VALID_TRUE_VALUES = (True, 'True', 'T', 't', 'true', '1')

DEF_SEED_PETITION_TEMPLATE = join(TEMPLATE_DIR, 'seed_petition.txt')
SEED_PETITION_TEMPLATE = getattr(settings, 'VAVILOV3_SEED_PETITION_TEMPLATE',
                                 DEF_SEED_PETITION_TEMPLATE)

DEF_SEED_PETITION_MAIL_SUBJECT = 'Seed petition'
SEED_PETITION_MAIL_SUBJECT = getattr(settings, 'VAVILOV3_SEED_PETITION_MAIL_SUBJECT',
                                     DEF_SEED_PETITION_MAIL_SUBJECT)

DEF_SEED_PETITION_DEBUG_MAIL = 'crf@mailinator.com'
SEED_PETITION_DEBUG_MAIL = getattr(settings, 'VAVILOV3_SEED_PETITION_DEBUG_MAIL',
                                   DEF_SEED_PETITION_DEBUG_MAIL)
EMAIL_DEBUG = getattr(settings, 'VAVILOV3_EMAIL_DEBUG', False)
