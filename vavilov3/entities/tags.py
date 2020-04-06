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

DATA_SOURCE = 'dataSource'
INSTITUTE_CODE = 'instituteCode'
IS_PUBLIC = 'is_public'
GROUP = 'group'
PUID = 'puid'
INSTITUTE_NAME = 'name'
INSTITUTE_TYPE = 'type'
INSTITUTE_ADDRESS = 'address'
INSTITUTE_ZIPCODE = 'zipcode'
INSTITUTE_EMAIL = 'email'
INSTITUTE_PHONE = 'phone'
INSTITUTE_CITY = 'city'
INSTITUTE_URL = 'url'
INSTITUTE_MANAGER = 'manager'
COLLECTIONS = 'collections'
GERMPLASM_NUMBER = 'germplasmNumber'
IS_AVAILABLE = 'is_available'
IS_ACTIVE = 'is_active'
IS_BASE = 'is_base'
IS_HISTORIC = 'is_historic'
IS_ARCHIVE = 'is_archive'
IS_SECONDARY = 'is_secondary'
IS_ACTIVE_AND_BASE = 'is_active_and_base'
IN_NUCLEAR_COLLECTION = 'in_nuclear_collection'
HAS_GERMPLASM_STORED = 'has_germplasm_stored'
CONSTATUS = 'conservation_status'
PASSPORTS = 'passports'
ACCESSIONSET_NUMBER = 'accessionsetNumber'
ACCESSIONS = 'accessions'
VALID_CONSERVATION_STATUSES = [IS_ACTIVE, IS_BASE, IS_HISTORIC, IS_ARCHIVE,
                               IS_ACTIVE_AND_BASE, IS_SECONDARY]

# phenotyping
# study
STUDY_NAME = 'name'
STUDY_DESCRIPTION = 'description'
STUDY_ACTIVE = 'active'
START_DATE = 'start_date'
END_DATE = 'end_date'
LOCATION = 'location'
CONTACT = 'contacts'
PROJECT_NAME = 'project_name'
SEASON = 'season'
INSTITUTION = 'institution'

# Observation Variable
OBSERVATION_VARIABLE_NAME = 'name'
TRAIT = 'trait'
OBSERVATION_VARIABLE_DESCRIPTION = 'description'
METHOD = 'method'
DATA_TYPE = 'data_type'
SCALE = 'scale'

# Observation Unit
OBSERVATION_UNIT_NAME = 'name'
ACCESSION = 'accession'
OBSERVATION_UNIT_LEVEL = 'level'
OBSERVATION_UNIT_REPLICATE = 'replicate'
OBSERVATION_UNIT_STUDY = 'study'
PLANTS = 'plants'

# Plant
PLANT_NAME = 'name'
PLANT_X = 'x'
PLANT_Y = 'y'
BLOCK_NUMBER = 'block_number'
ENTRY_NUMBER = 'entry_number'
PLANT_NUMBER = 'plant_number'
PLOT_NUMBER = 'plot_number'

# Observation
OBSERVATION_ID = 'observation_id'
OBSERVATION_VARIABLE = 'observation_variable'
OBSERVATION_UNIT = 'observation_unit'
OBSERVATION_CREATION_TIME = 'creation_time'
OBSERVER = 'observer'
VALUE = 'value'
OBSERVATION_STUDY = 'study'
VALUE_BEAUTY = 'value_beauty'
IMAGE = 'image'
IMAGE_FPATH = 'image_path'
IMAGE_MEDIUM = 'image_medium'
IMAGE_SMALL = 'image_small'
OBSERVATION_IMAGE_UID = 'observation_image_uid'

# scale
SCALE_NAME = 'name'
SCALE_DESCRIPTION = 'description'
SCALE_DATA_TYPE = 'data_type'
SCALE_DECIMAL_PLACES = 'decimal_places'
SCALE_MIN = 'min'
SCALE_MAX = 'max'
SCALE_VALID_VALUES = 'valid_values'

# TRAIT
TRAIT_NAME = 'name'
TRAIT_DESCRIPTION = 'description'
ONTOLOGY_NAME = 'ontology'
ONTOLOGY_ID = 'ontology_id'
YES_STRINGS = ('y', 'Y', 'Yes', 'yes', 'YES')
NO_STRINGS = ('n', 'N', 'No', 'no', 'NO')

# SEED PETITION
REQUEST_UID = 'request_uid'
REQUESTER_NAME = 'name'
REQUESTER_TYPE = 'type'
REQUESTER_INSTITUTION = 'institution'
REQUESTER_ADDRESS = 'address'
REQUESTER_CITY = 'city'
REQUESTER_POSTAL_CODE = 'postal_code'
REQUESTER_REGION = 'region'
REQUESTER_COUNTRY = 'country'
REQUESTER_EMAIL = 'email'
REQUEST_DATE = 'request_date'
REQUEST_AIM = 'aim'
REQUEST_COMMENTS = 'comments'
REQUESTED_ACCESSIONS = 'accessions'

ORDINAL = 'Ordinal'
NUMERICAL = 'Numerical'
NOMINAL = 'Nominal'
