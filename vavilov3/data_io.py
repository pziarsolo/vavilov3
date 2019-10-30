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

import iso3166
import csv

from django.contrib.auth import get_user_model

from vavilov3.models import Group, Country, Rank, ScaleDataType
from vavilov3.conf.settings import (ADMIN_GROUP,
                                    ALLOWED_TAXONOMIC_RANKS)
from vavilov3.entities.tags import ORDINAL, NOMINAL, NUMERICAL

OLD_COUNTRIES = {'CSHH': 'Czechoslovakia',
                 'YUCS': 'Yugoslavia',
                 'SUHH': 'Union of Soviet Socialist Republics',
                 'ANHH': 'Netherlands Antilles'}

SCALE_DATA_TYPES = [NUMERICAL, NOMINAL, ORDINAL]


def initialize_db(users_fhand=None):
    Group.objects.get_or_create(name=ADMIN_GROUP)
    if users_fhand:
        load_users(users_fhand)
    load_countries()
    load_ranks()
    load_scale_data_types()


def load_users(fhand):
    UserModel = get_user_model()
    for user in csv.DictReader(fhand, delimiter=','):
        group = Group.objects.get_or_create(name=user['group'])[0]
        if group.name == ADMIN_GROUP:
            user_db = UserModel.objects.create_superuser(user['username'],
                                                         user['mail'],
                                                         user['password'])
        else:
            user_db = UserModel.objects.create_user(user['username'], user['mail'],
                                                    user['password'])

        user_db.groups.add(group)


def load_countries():
    for country in iso3166.countries:
        Country.objects.create(name=country.name, code=country.alpha3)
    for code, name in OLD_COUNTRIES.items():
        Country.objects.create(name=name, code=code)


def load_ranks():
    for level, rank in enumerate(ALLOWED_TAXONOMIC_RANKS):
        Rank.objects.create(name=rank, level=level)


def load_scale_data_types():
    for data_type in SCALE_DATA_TYPES:
        ScaleDataType.objects.create(name=data_type)
