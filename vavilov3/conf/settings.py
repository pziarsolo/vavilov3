from django.conf import settings

ADMIN_GROUP = getattr(settings, 'VAVILOV3_ADMIN_GROUP', 'admin')

ALLOWED_TAXONOMIC_RANKS = ['family', 'genus', 'species', 'subspecies',
                           'variety', 'convarietas', 'group', 'forma']
USERS_CAN_CREATE_ACCESSIONSETS = getattr(
    settings, 'VAVILOV3_USERS_CAN_CREATE_ACCESSIONSETS', False)

DEF_ACCESSION_CSV_FIELDS = [
    'PUID', 'INSTCODE', 'ACCENUMB', 'CONSTATUS', 'IS_AVAILABLE', 'COLLNUMB',
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
