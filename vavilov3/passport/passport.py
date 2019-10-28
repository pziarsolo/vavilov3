import json
from copy import copy
from collections import OrderedDict
from datetime import datetime

from vavilov3.passport.tags import (CROP_NAME, ACQUISITION_DATE, BIO_STATUS,
                                    SPECIES, GENUS, INSTITUTE_CODE,
                                    GERMPLASM_NUMBER, DONOR, OTHER_NUMBERS,
                                    GERMPLASM_URL, GERMPLASM_ID, COLLECTION_SITE,
                                    COUNTRY, SITE, LATITUDE, LONGITUDE,
                                    ALTITUDE, COLLECTION_DATE, ANCESTRY,
                                    COLLECTION_SOURCE, GERMPLASM_NAME,
                                    COLLECTION_NUMBER, GERMPLASM_PUI,
                                    FIELD_COLLECTION_NUMBER, DATA_SOURCE, PROVINCE,
                                    MUNICIPALITY, GEOREF_METHOD, RETRIEVAL_DATE, STATE,
                                    ISLAND, OTHER, BREEDING_INSTITUTE, BREDDESCR,
                                    REMARKS, COORDUNCERTAINTY, COORD_SPATIAL_REFERENCE,
                                    LOCATION_SAVE_DUPLICATES, MLSSTATUS,
                                    GERMPLASM_STORAGE_TYPE, PEDIGREE)
from vavilov3.passport.validation import (ALLOWED_SUBTAXA, validate_passport_data,
                                          ALLOWED_TAXONOMIC_RANKS,
                                          ALLOWED_COLLECTING_SITE_KEYS)
from vavilov3.passport.pdci import calculate_pdci

VERSION = 1.0

RANK_TRANSLATOR = {'subspecies': 'subsp.', 'convarietas': 'convar.',
                   'variety': 'var.', 'group': 'Group', 'forma': 'f.'}


class Taxonomy(object):
    'class to deal with the subtaxas in vavilov2_client class'

    def __init__(self, taxonomy=None):
        if taxonomy is None:
            taxonomy = {}
        self._data = taxonomy

    def __bool__(self):
        return bool(self._data)

    @property
    def data(self):
        return self._data

    def __getitem__(self, key):
        if key in ALLOWED_SUBTAXA and key in self._data:
            return self._data[key]

    @property
    def genus(self):
        return self._data.get(GENUS, {}).get('name', None)

    @genus.setter
    def genus(self, genus):
        if GENUS not in self._data:
            self._data[GENUS] = {}
        self._data[GENUS]['name'] = genus

    @property
    def species(self):
        return self._data.get(SPECIES, {}).get('name', None)

    @species.setter
    def species(self, species):
        self._data[SPECIES] = {'name': species}

    @property
    def species_author(self):
        return self._data.get(SPECIES, {}).get('author', None)

    @species_author.setter
    def species_author(self, species_author):
        if not self.species:
            raise ValueError('Can not set species author if species is not set')
        self._data[SPECIES]['author'] = species_author

    @property
    def subtaxas(self):

        return {key: value for key, value in self._data.items() if key in ALLOWED_SUBTAXA}

    def get_subtaxa_name(self, rank):
        return self._data.get(rank, {}).get('name', None)

    def get_subtaxa_author(self, rank):
        return self._data.get(rank, {}).get('author', None)

    def set_subtaxa_name(self, rank, name):
        if rank in ALLOWED_SUBTAXA:
            self._data[rank] = {'name': name}

    def set_subtaxa_author(self, rank, author):
        if rank in ALLOWED_SUBTAXA and self.get_subtaxa_name(rank):
            self._data[rank]['author'] = author

    def add_subtaxa(self, subtaxa_rank, subtaxa_name, subtaxa_author=None):
        if subtaxa_rank not in ALLOWED_SUBTAXA:
            raise ValueError('{} Rank not allowed'.format(subtaxa_rank))
        if subtaxa_rank not in self._data:
            self._data[subtaxa_rank] = {}
        self._data[subtaxa_rank] = {'name': subtaxa_name}
        if subtaxa_author:
            self._data[subtaxa_rank]['author'] = subtaxa_author

    @property
    def long_name(self):
        # from multicrop passport descriptors 2.1
        # ‘subsp.’ (for subspecies); ‘convar.’ (for convariety);
        # ‘var.’ (for variety); ‘f.’ (for form);
        # ‘Group’ (for ‘cultivar group’)
        taxas = []
        for rank in ALLOWED_TAXONOMIC_RANKS:
            value = self.get_subtaxa_name(rank)
            if value:
                rank = RANK_TRANSLATOR.get(rank, None)
                if rank:
                    taxas.append(rank)
                taxas.append(value)
        return ' '.join(taxas) if taxas else None

    @property
    def taxons(self):
        taxons = OrderedDict()
        for rank in ALLOWED_TAXONOMIC_RANKS:
            taxa = self._data.get(rank, {}).get('name', None)
            author = self._data.get(rank, {}).get('author', None)
            if taxa:
                if author:
                    taxa += ' ' + author
                taxons[rank] = taxa
        return taxons

    @property
    def composed_taxons(self):
        taxas = []
        for rank in ALLOWED_TAXONOMIC_RANKS:
            value = self.get_subtaxa_name(rank)
            # print(value, rank)
            if value:
                rank_trans = RANK_TRANSLATOR.get(rank, None)
                if rank_trans:
                    taxas.extend([rank_trans, value])
                else:
                    taxas.append(value)
                yield rank, ' '.join(taxas)


class AccessionId(object):

    def __init__(self, id_dict=None, institute=None, number=None):
        if id_dict and (institute or number):
            raise ValueError('Can not initialize with dict and number or institute')
        if id_dict is None:
            id_dict = {}
        self._id_dict = id_dict
        if institute:
            self.institute = institute
        if number:
            self.number = number

    def __bool__(self):
        return bool(self._id_dict)

    def __eq__(self, other):
        return self.institute == other.institute and self.number == other.number

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def data(self):
        return self._id_dict

    @property
    def institute(self):
        return self._id_dict.get(INSTITUTE_CODE, None)

    @institute.setter
    def institute(self, institute_code):
        assert institute_code and isinstance(institute_code, str)
        self._id_dict[INSTITUTE_CODE] = institute_code

    @property
    def number(self):
        return self._id_dict.get(GERMPLASM_NUMBER, None)

    @number.setter
    def number(self, germplasm_number):
        assert germplasm_number and isinstance(germplasm_number, str)
        self._id_dict[GERMPLASM_NUMBER] = germplasm_number

    @property
    def field_number(self):
        return self._id_dict.get(FIELD_COLLECTION_NUMBER, None)

    @field_number.setter
    def field_number(self, field_number):
        assert field_number and isinstance(field_number, str)
        self._id_dict[FIELD_COLLECTION_NUMBER] = field_number

    @property
    def pui(self):
        return self._id_dict.get(GERMPLASM_PUI, None)

    @pui.setter
    def pui(self, pui):
        assert pui and isinstance(pui, str)
        self._id_dict[GERMPLASM_PUI] = pui

    @property
    def url(self):
        return self._id_dict.get(GERMPLASM_URL, None)

    @url.setter
    def url(self, url):
        assert url and isinstance(url, str)
        self._id_dict[GERMPLASM_URL] = url

    def keys(self):
        return self._id_dict.keys()

    def copy(self):
        return AccessionId(self._id_dict)


class Location():

    def __init__(self, location_dict=None):
        if location_dict is None:
            location_dict = {}
        self._data = location_dict

    def __bool__(self):
        return bool(self._data)

    def __str__(self):
        _site = []
        if self.country:
            _site.append(self.country)
        if self.province:
            _site.append(self.province)
        if self.site:
            _site.append(self.site)
        if self.municipality:
            _site.append(self.municipality)

        return ': '.join(_site)

    @property
    def data(self):
        _data = OrderedDict()
        for allowed_key in ALLOWED_COLLECTING_SITE_KEYS:
            value = self._data.get(allowed_key, None)
            if value:
                _data[allowed_key] = value
        # print(_data), print(self._data)
        return _data

    @property
    def country(self):
        return self._data.get(COUNTRY, None)

    @country.setter
    def country(self, code3):
        self._data[COUNTRY] = code3

    @property
    def province(self):
        return self._data.get(PROVINCE, None)

    @province.setter
    def province(self, code3):
        self._data[PROVINCE] = code3

    @property
    def municipality(self):
        return self._data.get(MUNICIPALITY, None)

    @municipality.setter
    def municipality(self, name):
        self._data[MUNICIPALITY] = name

    @property
    def site(self):
        return self._data.get(SITE, None)

    @site.setter
    def site(self, name):
        self._data[SITE] = name

    @property
    def latitude(self):
        return self._data.get(LATITUDE, None)

    @latitude.setter
    def latitude(self, latitude):
        self._data[LATITUDE] = latitude

    @property
    def longitude(self):
        return self._data.get(LONGITUDE, None)

    @longitude.setter
    def longitude(self, longitude):
        self._data[LONGITUDE] = longitude

    @property
    def altitude(self):
        return self._data.get(ALTITUDE, None)

    @altitude.setter
    def altitude(self, altitude):
        self._data[ALTITUDE] = altitude

    @property
    def georef_method(self):
        return self._data.get(GEOREF_METHOD, None)

    @georef_method.setter
    def georef_method(self, georef_method):
        self._data[GEOREF_METHOD] = georef_method

    @property
    def coord_uncertainty(self):
        return self._data.get(COORDUNCERTAINTY, None)

    @coord_uncertainty.setter
    def coord_uncertainty(self, coord_uncertainty):
        self._data[COORDUNCERTAINTY] = coord_uncertainty

    @property
    def coord_spatial_reference(self):
        return self._data.get(COORD_SPATIAL_REFERENCE, None)

    @coord_spatial_reference.setter
    def coord_spatial_reference(self, coord_spatial_reference):
        self._data[COORD_SPATIAL_REFERENCE] = coord_spatial_reference

    @property
    def state(self):
        return self._data.get(STATE, None)

    @state.setter
    def state(self, state):
        self._data[STATE] = state

    @property
    def island(self):
        return self._data.get(ISLAND, None)

    @island.setter
    def island(self, island):
        self._data[ISLAND] = island

    @property
    def other(self):
        return self._data.get(OTHER, None)

    @other.setter
    def other(self, other):
        self._data[OTHER] = other


class OtherNumbers():

    def __init__(self, other_numbers=None):
        if other_numbers is None:
            other_numbers = []
        self._data = [AccessionId(other_number) for other_number in other_numbers]

    @property
    def data(self):
        return [other_number.data for other_number in self._data]

    def __contains__(self, accession_id):
        return accession_id in self._data

    def __bool__(self):
        return bool(self.data)

    def append(self, accession_id):
        self._data.append(accession_id)

    def extend(self, accession_ids):
        self._data.extend(accession_ids)

    def __iter__(self):
        return iter(self._data)

    def __str__(self):
        return ";".join('{}:{}'.format(on[INSTITUTE_CODE], on[GERMPLASM_NUMBER]) for on in self.data)


class Passport():
    ''' Passport class to save vavilov2_client data structure '''
    class_name = 'Passport'

    def __init__(self, data=None, validate=True):
        if data is None:
            self._data = {}
        else:
            if validate:
                validate_passport_data(data)
            self._data = copy(data)

        _id = self._data[GERMPLASM_ID] if GERMPLASM_ID in self._data else {}
        self._accession_id = AccessionId(_id)

        _donor = self._data[DONOR] if DONOR in self._data else {}
        self._donor = AccessionId(_donor)

        _collection_number = self._data[COLLECTION_NUMBER] if COLLECTION_NUMBER in self._data else {}
        self._collection_number = AccessionId(_collection_number)

        _taxonomy = self._data['taxonomy'] if 'taxonomy' in self._data else {}
        self._taxonomy = Taxonomy(_taxonomy)

        _location = self._data[COLLECTION_SITE] if COLLECTION_SITE in self._data else {}
        self._location = Location(_location)

        _other_numbers = self._data[OTHER_NUMBERS] if OTHER_NUMBERS in self._data else []
        self._other_numbers = OtherNumbers(_other_numbers)

    def __str__(self):
        return self.data.__str__()

    @property
    def data(self):
        _data = self._data
        if self._accession_id:
            _data[GERMPLASM_ID] = self._accession_id.data
        if self._donor:
            _data[DONOR] = self._donor.data

        if self._collection_number:
            _data[COLLECTION_NUMBER] = self._collection_number.data

        if self._location:
            _data[COLLECTION_SITE] = self._location.data

        if self._other_numbers:
            _data[OTHER_NUMBERS] = self._other_numbers.data  # [accession_id.data for accession_id in self._other_numbers]

        if self._taxonomy:
            _data['taxonomy'] = self._taxonomy.data
        if _data:
            _data['version'] = str(VERSION)
        return _data

    @property
    def data_source(self):
        return self._data.get(DATA_SOURCE, {}).get('code', None)

    @data_source.setter
    def data_source(self, data_source):
        self._data[DATA_SOURCE] = {'code': data_source}

    @property
    def data_source_kind(self):
        return self._data.get(DATA_SOURCE, {}).get('kind', None)

    @data_source_kind.setter
    def data_source_kind(self, data_source_kind):
        if not self.data_source:
            raise ValueError('Can not set kind if data source is not defined')
        self._data[DATA_SOURCE]['kind'] = data_source_kind

    @property
    def retrieval_date(self):
        retrieval_date = self._data.get(DATA_SOURCE, {}).get(RETRIEVAL_DATE, None)
        if retrieval_date is not None:
            retrieval_date = retrieval_date.strftime("%Y-%m-%d")
        return retrieval_date

    @retrieval_date.setter
    def retrieval_date(self, retrieval_date):
        if not self.data_source:
            raise ValueError('Can not set retrieval date if data source is not defined')
        retrieval_date = datetime.strptime(retrieval_date, "%Y-%m-%d")
        self._data[DATA_SOURCE][RETRIEVAL_DATE] = retrieval_date

    @property
    def germplasm_id(self):
        return self._accession_id

    @germplasm_id.setter
    def germplasm_id(self, accession_id):
        self._accession_id = accession_id

    @property
    def institute_code(self):
        return self._accession_id.institute

    @institute_code.setter
    def institute_code(self, institute_code):
        self._accession_id.institute = institute_code

    @property
    def germplasm_number(self):
        return self._accession_id.number

    @germplasm_number.setter
    def germplasm_number(self, germplasm_number):
        self._accession_id.number = germplasm_number

    @property
    def germplasm_pui(self):
        return self._accession_id.pui

    @germplasm_pui.setter
    def germplasm_pui(self, germplasm_pui):
        self._accession_id.pui = germplasm_pui

    @property
    def germplasm_url(self):
        return self._accession_id.url

    @germplasm_url.setter
    def germplasm_url(self, germplasm_url):
        self._accession_id.url = germplasm_url

    @property
    def taxonomy(self):
        return self._taxonomy

    @property
    def crop_name(self):
        return self._data.get(CROP_NAME, None)

    @crop_name.setter
    def crop_name(self, crop_name):
        if crop_name is None:
            del self._data[CROP_NAME]
        else:
            assert isinstance(crop_name, str), 'crop_name must be and string'
            self._data[CROP_NAME] = crop_name

    @property
    def acquisition_date(self):
        return self.data.get(ACQUISITION_DATE, None)

    @acquisition_date.setter
    def acquisition_date(self, acquisiotion_date):
        self._data[ACQUISITION_DATE] = acquisiotion_date

    @property
    def bio_status(self):
        return self._data.get(BIO_STATUS, None)

    @bio_status.setter
    def bio_status(self, bio_status):
        self._data[BIO_STATUS] = bio_status

    @property
    def donor(self):
        return self._donor

    @donor.setter
    def donor(self, accession_id):
        self._donor = accession_id

    @property
    def donor_institute_description(self):
        return None

    @property
    def collection(self):
        return self._collection_number

    @property
    def collection_institute_description(self):
        return None

    @property
    def other_numbers(self):
        return self._other_numbers

    @other_numbers.setter
    def other_numbers(self, other_numbers):
        self._other_numbers = other_numbers

    @property
    def save_dup_sites(self):
        return self._data.get(LOCATION_SAVE_DUPLICATES, None)

    @save_dup_sites.setter
    def save_dup_sites(self, location_save_duplicates):
        sites = location_save_duplicates.split(':')
        self._data[LOCATION_SAVE_DUPLICATES] = sites

    @property
    def germplasm_storage_type(self):
        return self._data.get(GERMPLASM_STORAGE_TYPE, None)

    @germplasm_storage_type.setter
    def germplasm_storage_type(self, storage):
        self._data[GERMPLASM_STORAGE_TYPE] = storage

    @property
    def duplication_site_description(self):
        return None

    @property
    def mls_status(self):
        return self._data.get(MLSSTATUS, None)

    @mls_status.setter
    def mls_status(self, mls_status):
        self._data[MLSSTATUS] = mls_status

    @property
    def location(self):
        return self._location

    @property
    def collection_date(self):
        return self.data.get(COLLECTION_DATE, None)

    @collection_date.setter
    def collection_date(self, date):
        self.data[COLLECTION_DATE] = date

    @property
    def collection_source(self):
        return self._data.get(COLLECTION_SOURCE, None)

    @collection_source.setter
    def collection_source(self, source):
        self._data[COLLECTION_SOURCE] = source

    @property
    def ancest(self):
        return self.data.get(ANCESTRY, None)

    @ancest.setter
    def ancest(self, ancest):
        self._data[ANCESTRY] = ancest

    @property
    def germplasm_name(self):
        return self._data.get(GERMPLASM_NAME, None)

    @germplasm_name.setter
    def germplasm_name(self, name):
        self._data[GERMPLASM_NAME] = name

    @property
    def breeder_institute_code(self):
        return self._data.get(BREEDING_INSTITUTE, None)

    @breeder_institute_code.setter
    def breeder_institute_code(self, code):
        self._data[BREEDING_INSTITUTE] = code

    @property
    def breeder_institute_description(self):
        return self._data.get(BREDDESCR, None)

    @breeder_institute_description.setter
    def breeder_institute_description(self, description):
        self._data[BREDDESCR] = description

    @property
    def remarks(self):
        return self._data.get(REMARKS, None)

    @remarks.setter
    def remarks(self, remarks):
        self._data[REMARKS] = remarks

    @property
    def pedigree(self):
        return self._data.get(PEDIGREE, None)

    @pedigree.setter
    def pedigree(self, pedigree):
        self._data[PEDIGREE] = pedigree

    def validate(self, raise_if_error=True):
        validate_passport_data(self.data, raise_if_error)

    def json(self):
        return json.dumps(self.data)

    def copy(self):
        return Passport(self.data)

    @property
    def pdci(self):
        return calculate_pdci(self)
