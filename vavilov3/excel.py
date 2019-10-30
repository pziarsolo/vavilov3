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

import xlrd
from collections import OrderedDict


def excel_dict_reader(fhand, sheet_name=None, values_as_text=False):
    if isinstance(fhand, str):
        book = xlrd.open_workbook(filename=fhand)
    else:
        book = xlrd.open_workbook(file_contents=fhand.read())

    if sheet_name:
        sheet = book.sheet_by_name(sheet_name)
    else:
        sheet = book.sheets()[0]

    header = [header.value for header in sheet.row(0)]

    first = True
    for row in sheet.get_rows():
        if first:
            first = False
            continue
        if values_as_text:
            rowcells = []
            for cell in row:
                str_value = str(cell.value)
                if cell.ctype == 2 and cell.value == int(cell.value):
                    str_value = str_value.split('.')[0]
                rowcells.append(str_value)
        else:
            rowcells = [cell for cell in row]
        row_data = OrderedDict(zip(header, rowcells))
        yield row_data
