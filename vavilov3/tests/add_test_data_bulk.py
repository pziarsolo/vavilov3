#!/usr/bin/env python
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

VERIFY = True


def main():
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        admin_user = sys.argv[2]
        admin_pass = sys.argv[3]
    else:
        server_url = SERVER_URL
        admin_user = ADMINUSER
        admin_pass = ADMINPASS

    print('It needs django server with fresh db and celery running')
    # get token
    response = requests.post(server_url + 'api/auth/token/',
                             json={'username': admin_user,
                                   'password': admin_pass},
                             verify=VERIFY)
    token = response.json()['access']
    headers = {'Authorization': 'Bearer {}'.format(token)}

    # instal institute
    response = requests.post(server_url + 'api/institutes/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(INSTITUTE_FPATH, mode='rb')})

    process_task_response(response, headers, server_url)

    # install accession
    response = requests.post(server_url + 'api/accessions/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(ACCESSIONS_FPATH, mode='rb')},
                             data={'data_source_code': 'CRF',
                                   'data_source_kind': 'project'})

    process_task_response(response, headers, server_url)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(server_url + 'api/accessions/bulk/',
                                 headers=headers, verify=VERIFY,
                                 files={'file': open(ACCESSIONS_FPATH, mode='rb')},
                                 data={'data_source_code': 'CRF',
                                       'data_source_kind': 'project'})
        try:
            process_task_response(response, headers, server_url)
            raise ValueError()
        except RuntimeError:
            pass

    # install accessionset
    response = requests.post(server_url + 'api/accessionsets/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(ACCESSIONSETS_FPATH, mode='rb')})
    process_task_response(response, headers, server_url)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(server_url + 'api/accessionsets/bulk/',
                                 headers=headers, verify=VERIFY,
                                 files={'file': open(ACCESSIONSETS_FPATH, mode='rb')})

        try:
            process_task_response(response, headers, server_url)
            raise ValueError()
        except RuntimeError:
            pass

    # adding studies
    response = requests.post(server_url + 'api/studies/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(STUDIES_FPATH, mode='rb')})
    process_task_response(response, headers, server_url)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(server_url + 'api/studies/bulk/',
                                 headers=headers, verify=VERIFY,
                                 files={'file': open(STUDIES_FPATH, mode='rb')})
        try:
            process_task_response(response, headers, server_url)
            raise ValueError()
        except RuntimeError:
            pass

    # adding plants
    response = requests.post(server_url + 'api/plants/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(PLANTS_FPATH, mode='rb')})
    process_task_response(response, headers, server_url)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(server_url + 'api/plants/bulk/',
                                 headers=headers, verify=VERIFY,
                                 files={'file': open(PLANTS_FPATH, mode='rb')})
        try:
            process_task_response(response, headers, server_url)
            raise ValueError()
        except RuntimeError:
            pass

    # adding observation units
    response = requests.post(server_url + 'api/observation_units/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(OBSERVATION_UNITS_FPATH, mode='rb')})
    process_task_response(response, headers, server_url)

    if RUN_FAILLING_REQUESTS:
        # Adding again fails
        response = requests.post(server_url + 'api/observation_units/bulk/',
                                 headers=headers, verify=VERIFY,
                                 files={'file': open(OBSERVATION_UNITS_FPATH, mode='rb')})
        try:
            process_task_response(response, headers, server_url)
            raise ValueError()
        except RuntimeError:
            pass

#     # adding traits
    response = requests.post(server_url + 'api/traits/create_by_obo/',
                             headers=headers, verify=VERIFY,
                             files={'obo': open(TRAITS_FPATH)})
    process_task_response(response, headers, server_url)

    # adding scales
    response = requests.post(server_url + 'api/scales/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(SCALE_FPATH, mode='rb')})
    process_task_response(response, headers, server_url)

    # adding observation_variables
    response = requests.post(server_url + 'api/observation_variables/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(OBSERVATION_VARIABLES_FPATH, mode='rb')})
    process_task_response(response, headers, server_url)

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
    response = requests.post(server_url + 'api/observations/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(OBSERVATIONS_FPATH, mode='rb')})
    process_task_response(response, headers, server_url)

    # adding Observations: traits in columns
    response = requests.post(server_url + 'api/observations/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(OBSERVATIONS_IN_COLUMNS_FPATH, 'rb')},
                             data={TRAITS_IN_COLUMNS: True,
                                   CREATE_OBSERVATION_UNITS: 'foreach_observation'})

    process_task_response(response, headers, server_url)

    # Images
    response = requests.post(server_url + 'api/observation_images/bulk/',
                             headers=headers, verify=VERIFY,
                             files={'file': open(OBSERVATION_IMAGES_FPATH, mode='rb')},
                             data={CREATE_OBSERVATION_UNITS: 'foreach_observation'})

    process_task_response(response, headers, server_url)


def process_task_response(response, headers, server_url):
    if response.status_code != status.HTTP_200_OK:
        raise ValueError('there was a error\n: {}'.format(response.json()))
    task = response.json()
    task_response = requests.get(server_url + 'api/tasks/' + task['task_id'] + '/',
                                 headers=headers, verify=VERIFY)
    if task_response.status_code == status.HTTP_404_NOT_FOUND:
        time.sleep(0.1)
        task_response = requests.get(server_url + 'api/tasks/' + task['task_id'] + '/',
                                     headers=headers, verify=VERIFY)
    task = task_response.json()

    if task['status'] == 'SUCCESS':
        sys.stdout.write('{} OK: {}\n'.format(task['name'], task['result']))
    elif task['status'] == 'PENDING':
        time.sleep(1)
        process_task_response(response, headers, server_url)
    elif task['status'] == 'FAILURE':
        raise RuntimeError('{} task failed: {}'.format(task['name'],
                                                       task['result']))


if __name__ == '__main__':
    main()
