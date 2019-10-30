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

from vavilov3.passport.passport import Passport, OtherNumbers
from vavilov3.passport.validation import (ALLOWED_TAXONOMIC_RANKS,
                                          ALLOWED_COLLECTING_SITE_KEYS)

PASSPORT_PROPS = ['data_source',
                  'data_source_kind',
                  'institute_code',
                  'germplasm_number',
                  'germplasm_url',
                  'germplasm_pui',
                  'donor_institute_description',
                  'mls_status',
                  'acquisition_date',
                  'bio_status',
                  'collection_date',
                  'save_dup_sites',
                  'ancest',
                  'breeder_institute_description',
                  'crop_name',
                  'collection_institute_description',
                  'collection_source',
                  'remarks',
                  'germplasm_storage_type',
                  'duplication_site_description',
                  'breeder_institute_code',
                  'retrieval_date',
                  'germplasm_name']
'other_numbers',
'taxonomy.genus',
'location',
'germplasm_pui',
'germplasm_number',
'collection',
DONOR_PROPS = ['institute', 'number', 'field_number']
TAXONOMY_PROPS = ALLOWED_TAXONOMIC_RANKS
LOCATION_PROPS = ['country'] + ALLOWED_COLLECTING_SITE_KEYS[1:]
ACCESSION_NUMBER_PROPS = ['institute', 'number', 'field_number', 'url', 'pui']


def merge_passports(passports):
    if not passports:
        raise ValueError('No input passports')

    if len(passports) == 1:
        return passports[0]

    data_sources = [passport.data_source for passport in passports]

    merged = Passport()

    _merge_class_data(passports, merged, PASSPORT_PROPS, data_sources)
    _merge_class_data(passports, merged, TAXONOMY_PROPS, data_sources,
                      sub_class_name='taxonomy')
    _merge_class_data(passports, merged, LOCATION_PROPS, data_sources,
                      sub_class_name='location')
    _merge_class_data(passports, merged, ACCESSION_NUMBER_PROPS, data_sources,
                      sub_class_name='donor')
    _merge_class_data(passports, merged, ACCESSION_NUMBER_PROPS, data_sources,
                      sub_class_name='collection')
    other_numbers = OtherNumbers()
    for passport in passports:
        for other in passport.other_numbers:
            if other not in other_numbers:
                print('a')
                other_numbers.append(other)
    if other_numbers:
        merged.other_numbers = other_numbers

    return merged


def _merge_class_data(read_objects, write_object, props, data_sources, sub_class_name=None):

    for prop in props:
        values = []
        for index, read_object in enumerate(read_objects):
            if sub_class_name:
                read_object = getattr(read_object, sub_class_name)
            if read_object:
                value = getattr(read_object, prop, None)
                if value is not None:
                    data_source = data_sources[index]
                    values.append((value, data_source))
        if not any(values):
            continue
        if len(set(values)) > 1 and len(set([v[0] for v in values])) > 1:

            if prop != 'data_source':
                value = ', '.join(['{} ({})'.format(value, data_source)for value, data_source in values])
            else:
                value = ', '.join([v[0] for v in values])
        else:
            value = values[0][0]

        if sub_class_name:
            write_object_ = getattr(write_object, sub_class_name, None)
        else:
            write_object_ = write_object

        if write_object_ is not None:
            setattr(write_object_, prop, value)


def _merge_class_data2(read_objects, write_object, props, data_sources, sub_class_name=None):

    for prop in props:
        values = []
        for read_object in read_objects:
            if sub_class_name:
                read_object = getattr(read_object, sub_class_name)
            if read_object:
                values.append(getattr(read_object, prop, None))
        if not any(values):
            continue
        if len(set(values)) > 1:
            if prop != 'data_source':
                value = ', '.join(['{} ({})'.format(value, data_source)for value, data_source in zip(values, data_sources)])
            else:
                value = ', '.join(values)
        else:
            value = values[0]

        if sub_class_name:
            write_object_ = getattr(write_object, sub_class_name, None)
        else:
            write_object_ = write_object

        if write_object_ is not None:
            setattr(write_object_, prop, value)
