#!/usr/bin/env python
from os.path import join, dirname
import requests

SERVER_URL = 'http://localhost:8000/'
DATA_DIR = join(dirname(__file__), 'data')
INSTITUTE_FPATH = join(DATA_DIR, 'institutes.csv')
ACCESSIONS_FPATH = join(DATA_DIR, 'accessions.csv')
ACCESSIONSETS_FPATH = join(DATA_DIR, 'accessionsets.csv')


def main():
    # get token
    response = requests.post(SERVER_URL + 'api/auth/token/',
                             json={'username': 'crf', 'password': 'tomate..'})
    token = response.json()['access']
    headers = {'Authorization': 'Bearer {}'.format(token)}

    # instal institute
    response = requests.post(SERVER_URL + 'api/institutes/bulk/',
                             headers=headers,
                             files={'csv': open(INSTITUTE_FPATH)})
    print('Institute: ' + str(response.status_code))
    if response.status_code != 201:
        print(response.json())
    # install accession
    response = requests.post(SERVER_URL + 'api/accessions/bulk/',
                             headers=headers,
                             files={'csv': open(ACCESSIONS_FPATH)},
                             data={'data_source_code': 'CRF',
                                   'data_source_kind': 'project'})
    print('Accession: ' + str(response.status_code))
    if response.status_code != 201:
        print(response.json())
    # install accessionset
    response = requests.post(SERVER_URL + 'api/accessionsets/bulk/',
                             headers=headers,
                             files={'csv': open(ACCESSIONSETS_FPATH)})
    print('AccessionSet: ' + str(response.status_code))
    if response.status_code != 201:
        print(response.json())


if __name__ == '__main__':
    main()
