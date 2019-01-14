import iso3166
import csv

from django.contrib.auth.models import User

from vavilov3.models import Group, Country, Rank
from vavilov3.conf.settings import (ADMIN_GROUP,
                                    ALLOWED_TAXONOMIC_RANKS)

OLD_COUNTRIES = {'CSHH': 'Czechoslovakia',
                 'YUCS': 'Yugoslavia',
                 'SUHH': 'Union of Soviet Socialist Republics',
                 'ANHH': 'Netherlands Antilles'}


def initialize_db(users_fhand=None):
    Group.objects.get_or_create(name=ADMIN_GROUP)
    if users_fhand:
        load_users(users_fhand)
    load_countries()
    load_ranks()


def load_users(fhand):
    for user in csv.DictReader(fhand, delimiter=','):
        group = Group.objects.get_or_create(name=user['group'])[0]
        if group.name == ADMIN_GROUP:
            user_db = User.objects.create_superuser(user['username'],
                                                    user['mail'],
                                                    user['password'])
        else:
            user_db = User.objects.create_user(user['username'], user['mail'],
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
