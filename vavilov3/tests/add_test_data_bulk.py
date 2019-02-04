#!/usr/bin/env python
import sys
from os.path import join, dirname
import requests
import time

from rest_framework import status

SERVER_URL = 'http://localhost:8000/'
DATA_DIR = join(dirname(__file__), 'data')
INSTITUTE_FPATH = join(DATA_DIR, 'institutes.csv')
ACCESSIONS_FPATH = join(DATA_DIR, 'accessions.csv')
ACCESSIONSETS_FPATH = join(DATA_DIR, 'accessionsets.csv')
STUDIES_FPATH = join(DATA_DIR, 'studies.csv')
PLANTS_FPATH = join(DATA_DIR, 'plants.csv')
OBSERVATION_UNITS_FPATH = join(DATA_DIR, 'observation_units.csv')
OBSERVATION_VARIABLES_FPATH = join(DATA_DIR, 'observation_variables.csv')
OBSERVATIONS_FPATH = join(DATA_DIR, 'observations.csv')


def main():
    print('It needs django server with fresh db and celery running')
    # get token
    response = requests.post(SERVER_URL + 'api/auth/token/',
                             json={'username': 'crf', 'password': 'tomate..'})
    token = response.json()['access']
    headers = {'Authorization': 'Bearer {}'.format(token)}

    # instal institute
    response = requests.post(SERVER_URL + 'api/institutes/bulk/',
                             headers=headers,
                             files={'csv': open(INSTITUTE_FPATH)})

    process_task_response(response, headers)

    # install accession
    response = requests.post(SERVER_URL + 'api/accessions/bulk/',
                             headers=headers,
                             files={'csv': open(ACCESSIONS_FPATH)},
                             data={'data_source_code': 'CRF',
                                   'data_source_kind': 'project'})
    process_task_response(response, headers)

    # Adding again fails
    response = requests.post(SERVER_URL + 'api/accessions/bulk/',
                             headers=headers,
                             files={'csv': open(ACCESSIONS_FPATH)},
                             data={'data_source_code': 'CRF',
                                   'data_source_kind': 'project'})
    try:
        process_task_response(response, headers)
        raise ValueError()
    except RuntimeError:
        pass

    # install accessionset
    response = requests.post(SERVER_URL + 'api/accessionsets/bulk/',
                             headers=headers,
                             files={'csv': open(ACCESSIONSETS_FPATH)})
    process_task_response(response, headers)

    # Adding again fails
    response = requests.post(SERVER_URL + 'api/accessionsets/bulk/',
                             headers=headers,
                             files={'csv': open(ACCESSIONSETS_FPATH)})

    try:
        process_task_response(response, headers)
        raise ValueError()
    except RuntimeError:
        pass

    # adding studies
    response = requests.post(SERVER_URL + 'api/studies/bulk/',
                             headers=headers,
                             files={'csv': open(STUDIES_FPATH)})
    process_task_response(response, headers)

    # Adding again fails
    response = requests.post(SERVER_URL + 'api/studies/bulk/',
                             headers=headers,
                             files={'csv': open(STUDIES_FPATH)})
    try:
        process_task_response(response, headers)
        raise ValueError()
    except RuntimeError:
        pass

    # adding plants
    response = requests.post(SERVER_URL + 'api/plants/bulk/',
                             headers=headers,
                             files={'csv': open(PLANTS_FPATH)})
    process_task_response(response, headers)

    # Adding again fails
    response = requests.post(SERVER_URL + 'api/plants/bulk/',
                             headers=headers,
                             files={'csv': open(PLANTS_FPATH)})
    try:
        process_task_response(response, headers)
        raise ValueError()
    except RuntimeError:
        pass

    # adding studies
    response = requests.post(SERVER_URL + 'api/observation_units/bulk/',
                             headers=headers,
                             files={'csv': open(OBSERVATION_UNITS_FPATH)})
    process_task_response(response, headers)

    # Adding again fails
    response = requests.post(SERVER_URL + 'api/observation_units/bulk/',
                             headers=headers,
                             files={'csv': open(OBSERVATION_UNITS_FPATH)})
    try:
        process_task_response(response, headers)
        raise ValueError()
    except RuntimeError:
        pass

    # adding studies
    response = requests.post(SERVER_URL + 'api/observation_variables/bulk/',
                             headers=headers,
                             files={'csv': open(OBSERVATION_VARIABLES_FPATH)})
    process_task_response(response, headers)

    # Adding again fails
    response = requests.post(SERVER_URL + 'api/observation_units/bulk/',
                             headers=headers,
                             files={'csv': open(OBSERVATION_UNITS_FPATH)})
    try:
        process_task_response(response, headers)
        raise ValueError()
    except RuntimeError:
        pass

    # adding Observations
    response = requests.post(SERVER_URL + 'api/observations/bulk/',
                             headers=headers,
                             files={'csv': open(OBSERVATIONS_FPATH)})
    process_task_response(response, headers)


def process_task_response(response, headers):
    if response.status_code != status.HTTP_200_OK:
        raise ValueError('there was a error\n')
    task = response.json()
    task_response = requests.get(SERVER_URL + 'api/tasks/' + task['task_id'] + '/',
                                 headers=headers)
    if task_response.status_code == status.HTTP_404_NOT_FOUND:
        time.sleep(0.1)
        task_response = requests.get(SERVER_URL + 'api/tasks/' + task['task_id'] + '/',
                                     headers=headers)
    task = task_response.json()
    if task['status'] == 'SUCCESS':
        sys.stdout.write('{} OK: {}\n'.format(task['name'], task['result']))
    elif task['status'] == 'PENDING':
        time.sleep(1)
        process_task_response(response, headers)
    elif task['status'] == 'FAILURE':
        raise RuntimeError('{} task failed: {}'.format(task['name'],
                                                       task['result']))


if __name__ == '__main__':
    main()