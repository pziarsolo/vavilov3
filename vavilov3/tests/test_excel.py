from django.test import TestCase
from os.path import join, abspath, dirname

from vavilov3.entities.accession import (serialize_accessions_from_excel)

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'excels'))


class DataSourceViewTest(TestCase):

    def test_accession_parse(self):
        fpath = join(TEST_DATA_DIR, 'accessions_2019_09_04.xlsx')
        _ = serialize_accessions_from_excel(fpath, 'CRF', 'genebank')
#         print(accessions)
