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

from os.path import join, abspath, dirname

from vavilov3.tests import BaseTest
from vavilov3.data_io import initialize_db
from vavilov3.tests.data_io import (load_institutes_from_file,
                                    load_accessions_from_file,
                                    load_accessionsets_from_file)
from rest_framework.reverse import reverse

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'jsons'))


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

    def test_view_readonly(self):
        list_url = reverse('taxon-list')
        response = self.client.get(list_url)
        result = response.json()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], 'Solanum')

        list_url = reverse('taxon-list')
        result = self.client.get(list_url, data={'fields': 'name'})
        self.assertEqual(result.json(), [{'name': 'Solanum'},
                                         {'name': 'Solanum lycopersicum'},
                                         {'name': 'Solanum lycopersicum var. cerasiforme'}])

