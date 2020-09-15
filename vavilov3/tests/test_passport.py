import unittest
import copy

from vavilov3.passport.passport import Passport, AccessionId, Taxonomy
from vavilov3.passport.validation import (VALID_PASSPORT_DATA,
                                          PassportValidationError)
from vavilov3.passport.tags import OTHER_NUMBERS, GERMPLASM_ID


class PassportTest(unittest.TestCase):

    def test_init_empty(self):
        passport = Passport()
        assert not passport.data

    def test_init_with_data(self):
        passport = Passport(VALID_PASSPORT_DATA)
        assert passport.data == VALID_PASSPORT_DATA

    def test_data_not_writable(self):
        passport = Passport()
        try:
            passport.data = {'a': 12}
            self.fail('Attribute error should appear')
        except AttributeError:
            pass

    def test_genus(self):
        passport = Passport(VALID_PASSPORT_DATA)
        assert passport.taxonomy.genus == 'Medicago'
        passport.taxonomy.genus = 'Vitis'
        assert passport.taxonomy.genus == 'Vitis'
        assert passport.data['taxonomy']

    def test_species(self):
        data = copy.copy(VALID_PASSPORT_DATA)
        passport = Passport(data)
        assert passport.taxonomy.species == 'sativa'
        assert passport.taxonomy.species_author == 'L.'

        passport.taxonomy.species = 'silvestris'
        assert passport.taxonomy.species == 'silvestris'
        assert not passport.taxonomy.species_author
        passport.taxonomy.species_author = 'peio'
        assert passport.taxonomy.species_author == 'peio'

        passport.taxonomy.species = 'aa'
        assert not passport.taxonomy.species_author
        passport.taxonomy.species = 'bb'
        assert not passport.taxonomy.species_author

        passport = Passport()
        try:
            passport.taxonomy.species_author = 'peio'
            self.fail()
        except ValueError:
            pass

        passport.taxonomy.species = 'asda'
        assert passport.taxonomy.species == 'asda'

    def test_subtaxas(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert not passport.taxonomy.subtaxas

        passport.taxonomy.add_subtaxa('variety', 'pepe')
        assert passport.taxonomy.subtaxas
        assert passport.taxonomy.subtaxas == {'variety': {'name': 'pepe'}}
        assert passport.taxonomy['variety'] == {'name': 'pepe'}

    def test_crop_pname(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert passport.crop_name
        passport.crop_name = 'pepito'
        assert passport.crop_name == 'pepito'
        passport.crop_name = None
        try:
            passport.crop_name = 2
        except AssertionError:
            pass

    def test_acquisiotion_date(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert passport.acquisition_date == '198605--'
        try:
            passport.acquisition_date = '121'
        except ValueError:
            pass
        passport.acquisition_date = '19871212'

    def test_bio_status(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert passport.bio_status == '300'

        try:
            passport.bio_status = 300
        except ValueError:
            pass

        passport.bio_status = '200'

    def test_institute_code(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert passport.institute_code == 'ESP004'

        passport.institute_code = 'ESP005'
        assert passport.institute_code == 'ESP005'

        passport = Passport()
        passport.institute_code = 'ESP005'
        assert passport.institute_code == 'ESP005'

    def test_accession_number(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert passport.germplasm_number == 'NC019467'

        passport.germplasm_number = 'NC019468'
        assert passport.germplasm_number == 'NC019468'

        passport = Passport()
        passport.germplasm_number = 'NC019468'
        assert passport.germplasm_number == 'NC019468'

    def test_donor_number(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert passport.donor.institute == 'ESP007'
        passport.donor.institute = 'ESP008'
        assert passport.donor.institute == 'ESP008'
        passport.validate()

        passport = Passport()
        passport.donor.institute = 'ESP008'
        assert passport.donor.institute == 'ESP008'

    def test_other_numbers(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        assert passport.other_numbers.data == VALID_PASSPORT_DATA[OTHER_NUMBERS]
        new_other = AccessionId(institute='asda', number='asa')
        passport.other_numbers.append(new_other)
        assert new_other.data in passport.other_numbers.data

    def test_location(self):
        passport = Passport()
        passport.location.country = 'ESP'

    def test_validation(self):
        passport = Passport(copy.deepcopy(VALID_PASSPORT_DATA))
        passport.validate()

        passport = Passport()
        try:
            passport.validate()
        except PassportValidationError:
            pass

        passport = Passport()
        passport.institute_code = 'aa'
        try:
            passport.validate()
        except PassportValidationError:
            pass

        passport.germplasm_number = 'asda'
        passport.validate()

    def test_small_data(self):
        valid_data = {'version': '1.0',
                      'dataSource': {'code': 'asda', 'kind': 'asda', 'retrievalDate': 'asdasd'},
                      'otherNumbers': [],
                      'collectionSite': {},
                      'germplasmNumber': {'instituteCode': 'ESP004', 'germplasmNumber': 'asdasdasdasd'}}
        try:
            Passport(valid_data)
            self.fail()
        except PassportValidationError:
            pass


class AccessionIdTest(unittest.TestCase):

    def test_basic(self):
        accession = copy.deepcopy(VALID_PASSPORT_DATA[GERMPLASM_ID])
        acc_id = AccessionId(accession)
        assert acc_id.institute == 'ESP004'
        assert acc_id.keys() == VALID_PASSPORT_DATA[GERMPLASM_ID].keys()

        acc_id.institute = 'ESP005'
        assert acc_id.institute == 'ESP005'
        try:
            acc_id.url = ''
        except AssertionError:
            pass

    def test_is_empty(self):
        acc = AccessionId()
        assert not acc


class TaxonomyTest(unittest.TestCase):

    def test_basic(self):
        taxonomy = copy.deepcopy(VALID_PASSPORT_DATA['taxonomy'])
        taxonomy['family'] = {'name': 'ooo'}
        taxonomy = Taxonomy(taxonomy)
#         print(list(taxonomy.composed_taxons))


if __name__ == "__main__":
    import sys;sys.argv = ['', 'TaxonomyTest']
    unittest.main()
