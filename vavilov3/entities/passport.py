from collections import OrderedDict

from passports.passport import Passport, OtherNumbers, AccessionId
from passports.validation import validate_passport_data as validate_passport
from passports.merge import merge_passports as _merge_passports


class PassportValidationError(Exception):
    pass


def validate_passport_data(data):
    validate_passport(data)


def merge_passports(passports):
    _merge_passports(passports)


class PassportStruct(Passport):

    def __init__(self, api_data=None, instance=None, fields=None):
        if api_data and instance:
            raise ValueError('Can not initialize with data and instance')

        if instance:
            api_data = self._deserialize_instance(instance, fields)

        super().__init__(api_data)

    @staticmethod
    def _deserialize_instance(instance, fields):
        return instance.data
#         self.metadata.group = instance.group.name
#         self.metadata.is_public = instance.is_public

#         if fields is None or 'passport_institute' in fields:
#             self.institute_code = instance.institute.code
#         if fields is None or 'germplasmNumber' in fields:
#             self.germplasm_number = instance.number
    def to_list_representation(self, fields):
        items = []
        for field in fields:
            try:
                getter = PASSPORT_CSV_FIELD_CONFS.get(field)['getter']
            except TypeError:
                raise
            items.append(getter(self))
        return items

    def populate_with_csvrow(self, row):
        for field, value in row.items():
            if not value:
                continue
            field_conf = PASSPORT_CSV_FIELD_CONFS.get(field)
            if not field_conf:
                continue

            setter = field_conf['setter']
            try:
                setter(self, value)
            except BaseException as error:
                raise PassportValidationError('{}, error: {}'.format(self.germplasm_number, error))


COLLECTING_SITE_KEYS = ['state', 'province', 'island',
                        'municipality', 'other', 'site']


def build_collection_site(passport):
    if not passport.location:
        return ''
    site = []
    for key in COLLECTING_SITE_KEYS:
        location = getattr(passport.location, key, None)
        if location:
            site.append('{}:{}'.format(key, location))

    return ';'.join(site) if site else ''


def set_collection_site(passport, value):
    for descriptorsfields in value.split(';'):
        try:
            descriptor, value = descriptorsfields.split(':')
        except ValueError:
            raise ValueError('Collecion site of {} is not well formatted'.format(passport.germplasm_number))
        setattr(passport.location, descriptor, value)


def build_subtaxa(passport):
    subtaxa = []
    if passport.taxonomy.subtaxas:
        for rank, name in passport.taxonomy.subtaxas.items():
            rank = REVERSE_SUBTAXA[rank]
            if not rank.endswith('.'):
                rank += '.'
            subtaxa.extend([rank, name['name']])

    return ' '.join(subtaxa)


def set_subtaxa(passport, value):
    subtaxa = parse_subtaxa(value)
    for rank, name in subtaxa.items():
        passport.taxonomy.add_subtaxa(rank, name['name'])


SUBTAXAS = {'subsp.': 'subspecies',
            'subsp': 'subspecies',
            'var.': 'variety',
            'convar.': 'convarietas',
            'group.': 'group',
            'f.': 'forma'}
REVERSE_SUBTAXA = {v: k for k, v in SUBTAXAS.items()}


def parse_subtaxa(subtaxa):

    subtaxa_items = subtaxa.split()
    subtaxas = {}
    for index in range(0, len(subtaxa_items), 2):
        rank = subtaxa_items[index]
        try:
            name = subtaxa_items[index + 1]
        except IndexError:
            print(index, subtaxa_items)
        try:
            subtaxas[SUBTAXAS[rank]] = {'name': name}
        except KeyError:
            print(subtaxa)

    return subtaxas


def build_subtaxa_author(passport):
    author = None
    for subtaxa in passport.taxonomy.subtaxas.values():
        author = subtaxa.get('author', None)
    return author


def set_subtaxa_author(passport, value):
    lowest_rank = None
    for rank, subtaxa_data in passport.taxonomy.subtaxas.items():
        if 'name' in subtaxa_data:
            lowest_rank = rank
    if lowest_rank:
        passport.taxonomy.set_subtaxa_author(lowest_rank, value)


def build_remarks(passport):
    remarks = passport.remarks
    if remarks:
        return ";".join(['{}:{}'.format(k, v) for k, v in remarks.items()])


def set_remarks(passport, val):
    remarks = {}
    for descriptorsfields in val.split(';'):
        try:
            descriptor, value = descriptorsfields.split(':')
        except ValueError:
            raise ValueError('Remarks field in {} accession number is not well formated'.format(passport.germplasm_number))
        remarks[descriptor] = value
    if remarks:
        setattr(passport, 'remarks', remarks)


def set_other_numbers(passport, val):
    other_numbers = OtherNumbers()
    for other_number in val.split(';'):
        try:
            institute, number = other_number.split(':')
        except ValueError:
            print(other_number)
            raise ValueError('Other numbers field in {} accession number is not well formated'.format(passport.germplasm_number))
        acc = AccessionId(institute=institute, number=number)
        other_numbers.append(acc)
    passport.other_numbers = other_numbers


def build_other_numbers(passport):
    other_numbers = passport.other_numbers
    if other_numbers:
        return ";".join(['{}:{}'.format(on.institute, on.number) for on in other_numbers])


_PASSPORT_CSV_FIELD_CONFS = [
    {'csv_field_name': 'PUID', 'getter': lambda x: x.germplasm_pui,
     'setter': lambda obj, val: setattr(obj, 'germplasm_puid', val)},
    {'csv_field_name': 'INSTCODE', 'getter': lambda x: x.institute_code,
     'setter': lambda obj, val: setattr(obj, 'institute_code', val)},
    {'csv_field_name': 'ACCENUMB', 'getter': lambda x: x.germplasm_number,
     'setter': lambda obj, val: setattr(obj, 'germplasm_number', val)},
    {'csv_field_name': 'COLLNUMB', 'getter': lambda x: x.collection.field_number,
     'setter': lambda obj, val: setattr(obj.collection, 'field_number', val)},
    {'csv_field_name': 'COLLCODE', 'getter': lambda x: x.collection.institute,
     'setter': lambda obj, val: setattr(obj.collection, 'institute', val)},
    {'csv_field_name': 'GENUS', 'getter': lambda x: x.taxonomy.genus,
     'setter': lambda obj, val: setattr(obj.taxonomy, 'genus', val)},
    {'csv_field_name': 'SPECIES', 'getter': lambda x: x.taxonomy.species,
     'setter': lambda obj, val: setattr(obj.taxonomy, 'species', val)},
    {'csv_field_name': 'SPAUTHOR', 'getter': lambda x: x.taxonomy.species_author,
     'setter': lambda obj, val: setattr(obj.taxonomy, 'species_author', val)},
    {'csv_field_name': 'SUBTAXA', 'getter': build_subtaxa, 'setter': set_subtaxa},
    {'csv_field_name': 'SUBTAUTHOR', 'getter': build_subtaxa_author, 'setter': set_subtaxa_author},
    {'csv_field_name': 'CROPNAME', 'getter': lambda x: x.crop_name,
     'setter': lambda obj, val: setattr(obj, 'crop_name', val)},
    {'csv_field_name': 'ACCENAME', 'getter': lambda x: x.germplasm_name,
     'setter': lambda obj, val: setattr(obj, 'germplasm_name', val)},
    {'csv_field_name': 'ACQDATE', 'getter': lambda x: x.acquisition_date,
     'setter': lambda obj, val: setattr(obj, 'acquisition_date', val)},
    {'csv_field_name': 'ORIGCTY', 'getter': lambda x: x.location.country,
     'setter': lambda obj, val: setattr(obj.location, 'country', val)},
    {'csv_field_name': 'COLLSITE', 'getter': build_collection_site,
     'setter': set_collection_site},
    {'csv_field_name': 'LATITUDE', 'getter': lambda x: x.location.latitude,
     'setter': lambda obj, val: setattr(obj.location, 'latitude', float(val))},
    {'csv_field_name': 'LONGITUDE', 'getter': lambda x: x.location.longitude,
     'setter': lambda obj, val: setattr(obj.location, 'longitude', float(val))},
    {'csv_field_name': 'COORDUNCERT', 'getter': lambda x: x.location.coord_uncertainty,
     'setter': lambda obj, val: setattr(obj.location, 'coord_uncertainty', val)},
    {'csv_field_name': 'COORDDATUM', 'getter': lambda x: x.location.coord_spatial_reference,
     'setter': lambda obj, val: setattr(obj.location, 'country', val)},
    {'csv_field_name': 'GEOREFMETH', 'getter': lambda x: x.location.georef_method,
     'setter': lambda obj, val: setattr(obj.location, 'georef_method', val)},
    {'csv_field_name': 'ELEVATION', 'getter': lambda x: x.location.altitude,
     'setter': lambda obj, val: setattr(obj.location, 'altitude', int(float(val)))},
    {'csv_field_name': 'ACQDATE', 'getter': lambda x: x.acquisition_date,
     'setter': lambda obj, val: setattr(obj, 'acquisition_date', str(val))},
    {'csv_field_name': 'COLLDATE', 'getter': lambda x: x.collection_date,
     'setter': lambda obj, val: setattr(obj, 'collection_date', str(val))},
    {'csv_field_name': 'BREDCODE', 'getter': lambda x: x.breeder_institute_code,
     'setter': lambda obj, val: setattr(obj, 'breeder_institute_code', val)},
    {'csv_field_name': 'SAMPSTAT', 'getter': lambda x: x.bio_status,
     'setter': lambda obj, val: setattr(obj, 'bio_status', val)},
    {'csv_field_name': 'ANCEST', 'getter': lambda x: x.ancest,
     'setter': lambda obj, val: setattr(obj, 'ancest', val)},
    {'csv_field_name': 'COLLSRC', 'getter': lambda x: x.collection_source,
     'setter': lambda obj, val: setattr(obj, 'collection_source', val)},
    {'csv_field_name': 'DONORCODE', 'getter': lambda x: x.donor.institute,
     'setter': lambda obj, val: setattr(obj.donor, 'institute', val)},
    {'csv_field_name': 'DONORNUMB', 'getter': lambda x: x.donor.number,
     'setter': lambda obj, val: setattr(obj.donor, 'number', val)},
    {'csv_field_name': 'OTHERNUMB', 'getter': build_other_numbers,
     'setter': set_other_numbers},
    {'csv_field_name': 'DUPLSITE',
     'getter': lambda x: ":".join(x.save_dup_sites) if x.save_dup_sites is not None else '',
     'setter': lambda obj, val: setattr(obj, 'save_dup_sites', val)},
    {'csv_field_name': 'STORAGE', 'getter': lambda x: x.germplasm_storage_type,
     'setter': lambda obj, val: setattr(obj, 'germplasm_storage_type', val)},
    {'csv_field_name': 'MLSSTAT', 'getter': lambda x: x.mls_status,
     'setter': lambda obj, val: setattr(obj, 'mls_status', val)},
    {'csv_field_name': 'REMARKS', 'getter': build_remarks,
     'setter': set_remarks}
]

PASSPORT_CSV_FIELD_CONFS = OrderedDict([
    (f['csv_field_name'], f) for f in _PASSPORT_CSV_FIELD_CONFS])
