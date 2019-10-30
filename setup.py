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
import vavilov3
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vavilov3-pziarsolo",  # Replace with your own username
    version=vavilov3.version,
    author="P. Ziarsolo",
    author_email="pziarsolo@gmail.com",
    description="A django based REST api to deal with passport and phenotyping data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pziarsolo/vavilov3",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Framework :: Django",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
