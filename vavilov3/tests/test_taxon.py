from os.path import join, abspath, dirname

from vavilov3.tests import BaseTest
from vavilov3.data_io import initialize_db
from vavilov3.tests.data_io import (load_institutes_from_file,
                                    load_accessions_from_file,
                                    load_accessionsets_from_file)
from rest_framework.reverse import reverse

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data'))


class TaxaStatsTest(BaseTest):

    def setUp(self):
        self.initialize()
        initialize_db()
        institutes_fpath = join(TEST_DATA_DIR, 'institutes.json')
        load_institutes_from_file(institutes_fpath)
        accessions_fpath = join(TEST_DATA_DIR, 'accessions.json')
        load_accessions_from_file(accessions_fpath)
        accessionsets_fpath = join(TEST_DATA_DIR, 'accessionsets.json')
        load_accessionsets_from_file(accessionsets_fpath)

    def tests_stats(self):
        stats_url = reverse('taxon-stats-by-rank')
        response = self.client.get(stats_url)
        result = {'species': {'Solanum lycopersicum': {'num_accessions': 4, 'num_accessionsets': 2}}, 'variety': {'Solanum lycopersicum var. cerasiforme': {'num_accessions': 4, 'num_accessionsets': 2}}, 'genus': {'Solanum': {'num_accessions': 4, 'num_accessionsets': 2}}}
        assert result == response.json()
