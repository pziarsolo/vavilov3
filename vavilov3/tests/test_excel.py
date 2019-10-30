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

from django.test import TestCase
from os.path import join, abspath, dirname

from vavilov3.entities.accession import (serialize_accessions_from_excel)

TEST_DATA_DIR = abspath(join(dirname(__file__), 'data', 'excels'))


class DataSourceViewTest(TestCase):

    def test_accession_parse(self):
        fpath = join(TEST_DATA_DIR, 'accessions_2019_09_04.xlsx')
        _ = serialize_accessions_from_excel(fpath, 'CRF', 'genebank')
#         print(accessions)
