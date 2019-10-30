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

import re


def validate_id(code):
    errors = []
#     if re.search(' ', code):
#         errors.append('Can not use spaces inside ids')

#     if re.search('[a-z]', code):
#         errors.append('Ids must be all upper case')

    if re.search('[\/*"<>]', code):
        errors.append('"\", "/", "*", "<", ">", """ are not allowed characters')

#     if re.search('^[1-9]*$', code):
#         errors.append('Id can not be just a number')

    if errors:
        raise ValueError("{}: ".format(code) + "  ".join(errors))


def validate_name(name):
    errors = []
    if re.search('^[1-9]*$', name):
        errors.append('Id can not be just a number')

    if re.search('[\/*"<>]', name):
        errors.append('{}: "\\", "/", "*", "<", ">", """ are not allowed characters'.format(name))

    if errors:
        raise ValueError(" ".join(errors))

# validate_name('-')
#
# validate_name('asad asd')
