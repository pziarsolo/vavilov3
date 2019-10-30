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

import os
import subprocess
from subprocess import CalledProcessError


def get_version(path):

    def git_command(args):
        prefix = ['git', '-C', path]
        try:
            return subprocess.check_output(prefix + args).decode().strip()
        except CalledProcessError:
            return None

    try:
        import vavilov3._version
        return vavilov3._version.version
    except ImportError:
        version_full = git_command(['describe', '--tags', '--dirty=.dirty'])
        if version_full is None:
            return ''
        else:
            return version_full.replace('-', '.dev', 1).replace('-', '+')[1:]

# Return the git revision as a string
# def git_version():
#
#     def _minimal_ext_cmd(cmd):
#         # construct minimal environment
#         env = {}
#         for k in ['SYSTEMROOT', 'PATH']:
#             v = os.environ.get(k)
#             if v is not None:
#                 env[k] = v
#         # LANGUAGE is used on win32
#         env['LANGUAGE'] = 'C'
#         env['LANG'] = 'C'
#         env['LC_ALL'] = 'C'
#         try:
#             out = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
#         except Exception as error:
#             print(type(error))
#             raise
#         return out
#
#     try:
#         out = _minimal_ext_cmd(['git', 'describe', '--tags'])
#         GIT_REVISION = out.strip().decode('ascii')[1:]
#     except (OSError, CalledProcessError):
#         GIT_REVISION = "Unknown"
#
#     return GIT_REVISION


name = 'vavilov3'
default_app_config = 'vavilov3.apps.Vavilov3Config'
version = get_version(os.path.dirname(os.path.realpath(__file__)))
