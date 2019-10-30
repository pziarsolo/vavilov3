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

import setuptools
import subprocess
import os
from subprocess import CalledProcessError


def git_pep440_version(path):

    def git_command(args):
        prefix = ['git', '-C', path]
        try:
            return subprocess.check_output(prefix + args).decode().strip()
        except CalledProcessError:
            return None

    version_full = git_command(['describe', '--tags', '--dirty=.dirty'])
    if version_full is None:
        return ''
    else:
        return version_full.replace('-', '.dev', 1).split('-')[0][1:]


version = git_pep440_version(os.path.dirname(os.path.realpath(__file__)))
with open('vavilov3/_version.py', 'r') as fhand:
    version_in_file = fhand.readline().strip().split('=')[1]

if version != version_in_file:
    with open('vavilov3/_version.py', 'w') as fhand:
        fhand.write(f'version="{version}"')
        fhand.flush()

with open("README.md", "r") as fh:
    long_description = fh.read()

# packages = setuptools.find_packages()
# packages.pop(packages.index('vavilov3.tests'))
# print(packages)
setuptools.setup(
    name="vavilov3",
    version=version,
    author="P. Ziarsolo",
    author_email="pziarsolo@gmail.com",
    description="A django based REST api to deal with passport and phenotyping data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pziarsolo/vavilov3",
    license="GNU Affero General Public License v3 or later (AGPLv3+)",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Framework :: Django",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
