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

import unittest
import json
import sys
from datetime import datetime

from iso3166 import countries_by_alpha3

from vavilov3.passport.utils import BIOLOGICAL_STATUS, HABITATS, OLD_COUNTRIES

from vavilov3.passport.tags import (ACQUISITION_DATE, ALTITUDE, ANCESTRY, BIO_STATUS,
                                    BREEDING_INSTITUTE, COLLECTION_DATE, COLLECTION_NUMBER,
                                    COLLECTION_SITE, INSTITUTE_CODE, GERMPLASM_ID,
                                    GERMPLASM_NUMBER, GERMPLASM_PUI, GERMPLASM_URL,
                                    GERMPLASM_NAME, CROP_NAME, NCBI_TAXON, GENUS, SPECIES,
                                    DONOR, OTHER_NUMBERS, FIELD_COLLECTION_NUMBER,
                                    COUNTRY, LATITUDE, COLLECTION_SOURCE, DATA_SOURCE,
                                    LONGITUDE, SITE, RETRIEVAL_DATE, GEOREF_METHOD,
                                    REMARKS, PROVINCE, MUNICIPALITY, ISLAND, OTHER,
                                    STATE, BREDDESCR, COORDUNCERTAINTY,
                                    COORD_SPATIAL_REFERENCE, MLSSTATUS,
                                    GERMPLASM_STORAGE_TYPE, LOCATION_SAVE_DUPLICATES,
                                    PEDIGREE)


class PassportValidationError(Exception):
    pass


VALID_PASSPORT_DATA = {'version': '1.0',
                       DATA_SOURCE: {'code': 'COMAV', 'kind': 'genebank',
                                     RETRIEVAL_DATE: '20170102'},
                       GERMPLASM_ID: {INSTITUTE_CODE: 'ESP004',
                                      GERMPLASM_NUMBER: 'NC019467',
                                      GERMPLASM_PUI: 'ESP004:NC019467',
                                      GERMPLASM_URL: 'http://www.br.fgov.be/RESEARCH/COLLECTIONS/LIVING/PHASEOLUS/'},
                       GERMPLASM_NAME: 'Alfalfa de la buena',
                       CROP_NAME: 'Alfalfa',
                       'taxonomy': {NCBI_TAXON: 'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=3879',
                                    GENUS: {'name': 'Medicago'},
                                    SPECIES: {'author': 'L.', 'name': 'sativa'}},
                       DONOR: {INSTITUTE_CODE: 'ESP007', GERMPLASM_NUMBER: 'BGE010124'},
                       OTHER_NUMBERS: [{INSTITUTE_CODE: 'ESP004',
                                        GERMPLASM_NUMBER: 'BGE010124'}],
                       COLLECTION_NUMBER: {INSTITUTE_CODE: 'ESP026',
                                           GERMPLASM_NUMBER: 'BGV010101',
                                           FIELD_COLLECTION_NUMBER: 'ECU-100'},
                       COLLECTION_SITE: {COUNTRY: 'ESP',
                                         PROVINCE: 'Valladolid',  # Province or State
                                         MUNICIPALITY: 'Bolaños de Campos',  # Municipality, County or District
                                         SITE: 'close to the city',
                                         LATITUDE: 42.0075, LONGITUDE: 5.283888888888889,
                                         COORDUNCERTAINTY: '1',
                                         GEOREF_METHOD: 'GPS',
                                         COORD_SPATIAL_REFERENCE: 'WGS84',
                                         ALTITUDE: 19},
                       ACQUISITION_DATE: '198605--',
                       BIO_STATUS: '300',
                       COLLECTION_SOURCE: '40',
                       COLLECTION_DATE: '20171122',
                       BREEDING_INSTITUTE: {INSTITUTE_CODE: 'ESP004'},
                       ANCESTRY: 'some tomato',
                       REMARKS: {'collection': 'notes of the collection',
                                 'genebank_management': 'aaa'},
                       BREDDESCR: 'asasda',
                       MLSSTATUS: 'Y',
                       GERMPLASM_STORAGE_TYPE: 'aaa',
                       PEDIGREE: 'pedigree'
                       }

INVALID1 = {"version": "1.0",
            GERMPLASM_ID: {GERMPLASM_NUMBER: "4328"},
            "collectionSite": {COUNTRY: "GBR"},
            "taxonomy": {
                "genus": {"name": "Lycopersicon"},
                "species": {"name": "esculentum", "author": "Mill."}},
            "dataSource": {"kind": "passport_collector", "id": "ECPGR"},
            "collectionSource": "50",
            GERMPLASM_NAME: "HISTON CROPPER",
            OTHER_NUMBERS: [{GERMPLASM_NUMBER: "UNW 65/9-23"}]
            }

ALLOWED_FIELDS = set(VALID_PASSPORT_DATA.keys())
ALLOWED_DATA_SOURCE_KINDS = ['genebank', 'study', 'project',
                             'passport_collector']

ALLOWED_SUBTAXA = ['subspecies', 'variety', 'convarietas', 'group', 'forma']
ALLOWED_TAXONOMIC_RANKS = ['family', 'genus', 'species'] + ALLOWED_SUBTAXA
ALLOWED_COLLECTING_SITE_KEYS = [COUNTRY, STATE, PROVINCE, ISLAND,
                                MUNICIPALITY, OTHER, SITE, LATITUDE,
                                LONGITUDE, ALTITUDE, GEOREF_METHOD,
                                COORDUNCERTAINTY, COORD_SPATIAL_REFERENCE]
ALLOWED_REMARKS_KEYS = ['collection', 'genebank_management']

ALLOWED_COUNTRIES = list(countries_by_alpha3.keys())
OLD_COUNTRIES = set(OLD_COUNTRIES.values())
ALLOWED_COUNTRIES.extend(OLD_COUNTRIES)

NOW_YEAR = datetime.now().year


def _check_accession_number(accession_number, required_fields=(INSTITUTE_CODE,
                                                               GERMPLASM_NUMBER)):
    if GERMPLASM_NUMBER in accession_number:
        assert isinstance(accession_number[GERMPLASM_NUMBER], str)
    if required_fields:
        required_fields = set(required_fields)
        missing_fields = required_fields.difference(accession_number.keys())
        if missing_fields:
            msg = 'Some required fields are missing: ' + \
                ','.join(missing_fields)
            raise ValueError(msg)


def _check_collecting_number(number):
    assert len(number.keys()) > 0, GERMPLASM_NUMBER + ' or field_collection_number is required'
    assert not set(number.keys()).difference(
        [INSTITUTE_CODE, GERMPLASM_NUMBER, FIELD_COLLECTION_NUMBER]), 'Uknown field in collection_number'


def _check_no_empty_fields(passport, key=None):
    if isinstance(passport, str):
        assert passport, 'Empty field: ' + key
        return
    if isinstance(passport, (float, int)):
        assert passport is not None, 'Empty field: ' + key
        return

    if isinstance(passport, list):
        items = zip(passport, [key] * len(passport))
    else:
        items = passport.items()

    for key, item in items:
        _check_no_empty_fields(item, key=key)


def _check_three_letter_country_code(country):
    msg = 'Not valid iso3166 three letter country code: {}'.format(country)
    assert country in ALLOWED_COUNTRIES, msg


def check_date(date):
    assert isinstance(date, str), 'date has to be a string'
    assert len(date) == 8, 'date has to be a string of length 8'
    assert 1800 < int(
        date[:4]) <= NOW_YEAR, 'First four characters of a date should be a year ' + date[:4]


def check_bio_status(bio_status):
    if not isinstance(bio_status, str):
        raise AssertionError('biological_status has to be a string')
    if bio_status not in BIOLOGICAL_STATUS.keys():
        raise AssertionError(
            'Unknown biological_status: ' + str(bio_status))


def _validate_version_1(passport, raise_if_error):
    unknown_fields = set(passport.keys()).difference(ALLOWED_FIELDS)
    if unknown_fields:
        msg = 'There are unknown_fields: ' + ','.join(unknown_fields)
        raise AssertionError(msg)

    _check_no_empty_fields(passport)
    if 'dataSource' in passport:
        assert isinstance(passport['dataSource']['code'], str)
        if 'kind' in passport['dataSource']:
            assert passport['dataSource']['kind'] in ALLOWED_DATA_SOURCE_KINDS, 'data source kinds not in allowed types'
        if RETRIEVAL_DATE in passport['dataSource']:
            retrieval_date = passport['dataSource'][RETRIEVAL_DATE]

            assert isinstance(retrieval_date, str), 'Data source retrieval date must be string'
            try:
                datetime.strptime(retrieval_date, "%Y-%m-%d")
            except ValueError as error:
                raise AssertionError('datasource retrieval date format must be YYYY-MM-DD')

    if INSTITUTE_CODE in passport[GERMPLASM_ID]:
        assert isinstance(passport[GERMPLASM_ID][INSTITUTE_CODE], str), 'institute_code is required'

    if 'taxonomy' in passport:
        uknown_ranks = set(passport['taxonomy'].keys()).difference(
            ALLOWED_TAXONOMIC_RANKS)
        uknown_ranks = uknown_ranks.difference([NCBI_TAXON])
        if uknown_ranks:
            raise AssertionError(
                'Unknown taxonomic ranks: ' + ','.join(uknown_ranks))

        for rank, taxon in passport['taxonomy'].items():
            if rank == NCBI_TAXON:
                continue
            assert not set(taxon.keys()).difference(['name', 'author'])

    if 'donor' in passport:
        _check_accession_number(passport['donor'], required_fields=None)

    if 'collectionNumber' in passport:
        _check_collecting_number(passport['collectionNumber'])

    if OTHER_NUMBERS in passport:
        for number in passport[OTHER_NUMBERS]:
            _check_accession_number(number, required_fields=(GERMPLASM_NUMBER,))

    if COLLECTION_SITE in passport:
        msg = 'Unknown collection_site key: '
        unknown_fields = set(passport[COLLECTION_SITE].keys()).difference(ALLOWED_COLLECTING_SITE_KEYS)
        if unknown_fields:
            raise AssertionError(msg + ','.join(unknown_fields))
        if COUNTRY in passport[COLLECTION_SITE]:
            _check_three_letter_country_code(
                passport[COLLECTION_SITE][COUNTRY])
        if 'latitude' in passport[COLLECTION_SITE]:
            msg = 'latitude is required in geolocation and has to be a number'
            assert isinstance(passport[COLLECTION_SITE]['latitude'], (float, int)), msg
        if 'longitude' in passport[COLLECTION_SITE]:
            msg = 'longitude is required in geolocation and has to be a number'
            assert isinstance(passport[COLLECTION_SITE]['longitude'], (float, int)), msg

        if 'altitude' in passport[COLLECTION_SITE]:
            msg = 'altitude has to be a number'
            assert isinstance(passport[COLLECTION_SITE]['altitude'], (int, float))

    if 'acquisitionDate' in passport:
        try:
            check_date(passport['acquisitionDate'])
        except AssertionError as error:
            sys.stderr.write('{}: {} {}\n'.format(passport[GERMPLASM_ID][GERMPLASM_NUMBER],
                                                  passport['acquisitionDate'],
                                                  error))
            if raise_if_error:
                raise

    if 'collectionDate' in passport:
        try:
            check_date(passport['collectionDate'])
        except AssertionError as error:
            sys.stderr.write('{}: {} {}\n'.format(passport[GERMPLASM_ID][GERMPLASM_NUMBER],
                                                  passport['collectionDate'],
                                                  error))
            if raise_if_error:
                raise

    if BIO_STATUS in passport:
        check_bio_status(passport[BIO_STATUS])

    if 'collectionSource' in passport:
        if passport['collectionSource'] not in HABITATS.keys():
            raise AssertionError(
                'Unknown collectionSource: ' + passport['collectionSource'])
    if 'remarks' in passport:
        unknown_fields = set(passport['remarks'].keys()).difference(ALLOWED_REMARKS_KEYS)
        if unknown_fields:
            raise AssertionError('Unknown remarks fields: ' + str(unknown_fields))
    if MLSSTATUS in passport:
        if passport[MLSSTATUS] not in ('Y', 'N'):
            raise AssertionError('MLSStatus only can be Y for yes and N for No')
    if LOCATION_SAVE_DUPLICATES in passport:
        assert isinstance(passport[LOCATION_SAVE_DUPLICATES], (list, tuple)), 'dup_sites must be a list'


def validate_passport_data(passport, raise_if_error=True):
    try:
        assert 'version' in passport, 'version is a required key'
        assert GERMPLASM_ID in passport, 'accession_number is a required key'
        assert isinstance(passport[GERMPLASM_ID][GERMPLASM_NUMBER], str), 'germplasm_number ir required'
        assert isinstance(passport[GERMPLASM_ID][INSTITUTE_CODE], str), 'institute_code is required'
        if passport['version'] == '1.0':
            _validate_version_1(passport, raise_if_error=raise_if_error)
    except AssertionError as error:
        try:
            number = passport[GERMPLASM_NUMBER]
        except KeyError:
            number = ''
        raise PassportValidationError('{}: {}'.format(number, str(error)))
    except KeyError as error:
        try:
            number = passport[GERMPLASM_NUMBER]
        except KeyError:
            number = ''
        error = str(error) + ' not found'
        raise PassportValidationError('{}: {}'.format(number, error))


def write_and_validate_passports(passports, out_fhand, raise_if_error=True):
    validated_passports = []
    for passport in passports:
        try:
            passport.validate(raise_if_error)
        except PassportValidationError:
            import pprint
            pprint.pprint(passport)
            raise
        validated_passports.append(passport)
    json.dump([passport.data for passport in validated_passports], out_fhand,
              indent=4, sort_keys=True)


class ValidatorTest(unittest.TestCase):

    def test_validator(self):
        validate_passport_data(VALID_PASSPORT_DATA)
        try:
            validate_passport_data(INVALID1)
            self.fail()
        except KeyError:
            pass


if __name__ == '__main__':
    unittest.main()
