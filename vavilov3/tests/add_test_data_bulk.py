#!/usr/bin/env python
import sys
import time
from os.path import join, dirname

import requests

from rest_framework import status

SERVER_URL = 'http://localhost:8000/'
DATA_DIR = join(dirname(__file__), 'data')
EXCEL_DIRS = join(DATA_DIR, 'excels')
INSTITUTE_FPATH = join(EXCEL_DIRS, 'institutes.xlsx')
ACCESSIONS_FPATH = join(EXCEL_DIRS, 'accessions.xlsx')
ACCESSIONSETS_FPATH = join(EXCEL_DIRS, 'accessionsets.xlsx')
STUDIES_FPATH = join(EXCEL_DIRS, 'studies.xlsx')
PLANTS_FPATH = join(EXCEL_DIRS, 'plants.xlsx')
OBSERVATION_UNITS_FPATH = join(EXCEL_DIRS, 'observation_units.xlsx')
OBSERVATION_VARIABLES_FPATH = join(EXCEL_DIRS, 'observation_variables.xlsx')
OBSERVATIONS_FPATH = join(EXCEL_DIRS, 'observations.xlsx')
OBSERVATIONS_IN_COLUMNS_FPATH = join(EXCEL_DIRS, 'observations_in_columns.xlsx')
OBSERVATION_IMAGES_FPATH = join(DATA_DIR, 'images.zip')
TRAITS_FPATH = join(DATA_DIR, 'to.obo')
SCALE_FPATH = join(EXCEL_DIRS, 'scales.xlsx')
ADMINUSER = 'admin'
ADMINPASS = 'pass'

RUN_FAILLING_REQUESTS = True
RUN_FAILLING_REQUESTS = False

TRAITS_IN_COLUMNS = 'traits_in_columns'
CREATE_OBSERVATION_UNITS = 'create_observation_units'


def main():
    print('It needs django server with fresh db and celery running')
    # get token
    response = requests.post(SERVER_URL + 'api/auth/token/',
                             json={'username': ADMINUSER, 'password': ADMINPASS})
    token = response.json()['access']
    headers = {'Authorization': 'Bearer {}'.format(token)}

    # instal institute
    response = requests.post(SERVER_URL + 'api/institutes/bulk/',
                             headers=headers,
                             files={'file': open(INSTITUTE_FPATH, mode='rb')})

    process_task_response(response, headers)

    # install accession
    response = requests.post(SERVER_URL + 'api/accessions/bulk/',
                             headers=headers,
                             files={'file': open(ACCESSIONS_FPATH, mode='rb')},
                             data={'data_source_code': 'CRF',
                                   'data_source_kind': 'project'})

    process_task_response(response, headers)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(SERVER_URL + 'api/accessions/bulk/',
                                 headers=headers,
                                 files={'file': open(ACCESSIONS_FPATH, mode='rb')},
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
                             files={'file': open(ACCESSIONSETS_FPATH, mode='rb')})
    process_task_response(response, headers)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(SERVER_URL + 'api/accessionsets/bulk/',
                                 headers=headers,
                                 files={'file': open(ACCESSIONSETS_FPATH, mode='rb')})

        try:
            process_task_response(response, headers)
            raise ValueError()
        except RuntimeError:
            pass

    # adding studies
    response = requests.post(SERVER_URL + 'api/studies/bulk/',
                             headers=headers,
                             files={'file': open(STUDIES_FPATH, mode='rb')})
    process_task_response(response, headers)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(SERVER_URL + 'api/studies/bulk/',
                                 headers=headers,
                                 files={'file': open(STUDIES_FPATH, mode='rb')})
        try:
            process_task_response(response, headers)
            raise ValueError()
        except RuntimeError:
            pass

    # adding plants
    response = requests.post(SERVER_URL + 'api/plants/bulk/',
                             headers=headers,
                             files={'file': open(PLANTS_FPATH, mode='rb')})
    process_task_response(response, headers)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(SERVER_URL + 'api/plants/bulk/',
                                 headers=headers,
                                 files={'file': open(PLANTS_FPATH, mode='rb')})
        try:
            process_task_response(response, headers)
            raise ValueError()
        except RuntimeError:
            pass

    # adding observation units
    response = requests.post(SERVER_URL + 'api/observation_units/bulk/',
                             headers=headers,
                             files={'file': open(OBSERVATION_UNITS_FPATH, mode='rb')})
    process_task_response(response, headers)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(SERVER_URL + 'api/observation_units/bulk/',
                                 headers=headers,
                                 files={'file': open(OBSERVATION_UNITS_FPATH, mode='rb')})
        try:
            process_task_response(response, headers)
            raise ValueError()
        except RuntimeError:
            pass

#     # adding traits
    response = requests.post(SERVER_URL + 'api/traits/create_by_obo/',
                             headers=headers,
                             files={'obo': open(TRAITS_FPATH)})
    process_task_response(response, headers)

    # adding scales
    response = requests.post(SERVER_URL + 'api/scales/bulk/',
                             headers=headers,
                             files={'file': open(SCALE_FPATH, mode='rb')})
    process_task_response(response, headers)

    # adding observation_variables
    response = requests.post(SERVER_URL + 'api/observation_variables/bulk/',
                             headers=headers,
                             files={'file': open(OBSERVATION_VARIABLES_FPATH, mode='rb')})
    process_task_response(response, headers)

#     if RUN_FAILLING_REQUESTS:
#         # Adding again fails
#         response = requests.post(SERVER_URL + 'api/observation_units/bulk/',
#                                  headers=headers,
#                                  files={'file': open(OBSERVATION_UNITS_FPATH, mode='rb')})
#         try:
#             process_task_response(response, headers)
#             raise ValueError()
#         except RuntimeError:
#             pass

    # adding Observations
    response = requests.post(SERVER_URL + 'api/observations/bulk/',
                             headers=headers,
                             files={'file': open(OBSERVATIONS_FPATH, mode='rb')})
    process_task_response(response, headers)

    # adding Observations: traits in columns
    response = requests.post(SERVER_URL + 'api/observations/bulk/',
                             headers=headers,
                             files={'file': open(OBSERVATIONS_IN_COLUMNS_FPATH, 'rb')},
                             data={TRAITS_IN_COLUMNS: True,
                                   CREATE_OBSERVATION_UNITS: 'foreach_observation'})

    process_task_response(response, headers)

    # Images
    response = requests.post(SERVER_URL + 'api/observation_images/bulk/',
                             headers=headers,
                             files={'file': open(OBSERVATION_IMAGES_FPATH, mode='rb')},
                             data={CREATE_OBSERVATION_UNITS: 'foreach_observation'})

    process_task_response(response, headers)


def process_task_response(response, headers):
    if response.status_code != status.HTTP_200_OK:
        raise ValueError('there was a error\n: {}'.format(response.json()))
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
