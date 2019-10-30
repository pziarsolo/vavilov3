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

import unittest

from unittest.mock import MagicMock

from django.contrib.auth.models import AnonymousUser

from vavilov3.permissions import UserGroupObjectPublicPermission


class PermissionsTest(unittest.TestCase):

    def setUp(self):
        self.permisions = UserGroupObjectPublicPermission()

    @staticmethod
    def set_up_mocks(obj_owner, obj_is_public, action, user_is_staff,
                     user_groups=[], anonUser=False,
                     request_data_is_public=False):
        obj = MagicMock(owner=obj_owner, is_public=obj_is_public)
        request = MagicMock(user=MagicMock(is_staff=user_is_staff,
                                           token={'groups': user_groups}),
                            data={'metadata': {'is_public': request_data_is_public}})
        if anonUser:
            request.user = AnonymousUser()
        view = MagicMock(action=action)
        return request, view, obj

    def testUser_is_staff(self):
        for action in ['retrieve', 'update', 'partial_update', 'destroy']:
            mocks = self.set_up_mocks(obj_owner='CRF',
                                      obj_is_public=True,
                                      action=action,
                                      user_is_staff=True,
                                      user_groups=['CRF'])
            self.assertTrue(self.permisions.has_object_permission(*mocks))

    def testUser_ownObj(self):
        # if it is yours and is not public, allow anything
        for action in ['retrieve', 'update', 'partial_update', 'destroy']:
            mocks = self.set_up_mocks(obj_owner='COMAV',
                                      obj_is_public=False,
                                      action=action,
                                      user_is_staff=False,
                                      user_groups=['COMAV'])
            if action in ['partial_update']:
                self.assertFalse(self.permisions.has_object_permission(*mocks),
                                 mocks)
            else:
                self.assertTrue(self.permisions.has_object_permission(*mocks),
                                mocks)
        # trying to change public when you are not staff
        mocks = self.set_up_mocks(obj_owner='COMAV',
                                  obj_is_public=False,
                                  action='update',
                                  user_is_staff=False,
                                  user_groups=['COMAV'],
                                  request_data_is_public=True)
        self.assertFalse(self.permisions.has_object_permission(*mocks), mocks)
        # if it is yours and is public, READ anything, Modify nothing
        for action in ['retrieve', 'update', 'partial_update', 'destroy']:
            mocks = self.set_up_mocks(obj_owner='COMAV',
                                      obj_is_public=True,
                                      action=action,
                                      user_is_staff=False,
                                      user_groups=['COMAV'])
            if action in ['retrieve', 'list']:
                self.assertTrue(self.permisions.has_object_permission(*mocks),
                                mocks)
            elif action in ['update', 'partial_update', 'destroy']:
                self.assertFalse(self.permisions.has_object_permission(*mocks),
                                 mocks)

    def test_user_is_anonymous(self):
        for action in ['retrieve', 'update', 'partial_update', 'destroy']:
            mocks = self.set_up_mocks(obj_owner='COMAV',
                                      obj_is_public=True,
                                      action=action,
                                      user_is_staff=False,
                                      user_groups=[],
                                      anonUser=True)
            if action in ['retrieve', 'list']:
                self.assertTrue(self.permisions.has_object_permission(*mocks),
                                mocks)
            elif action in ['update', 'partial_update', 'destroy']:
                self.assertFalse(self.permisions.has_object_permission(*mocks),
                                 mocks)

        for action in ['retrieve', 'list', 'update', 'partial_update',
                       'destroy']:
            mocks = self.set_up_mocks(obj_owner='COMAV',
                                      obj_is_public=False,
                                      action=action,
                                      user_is_staff=False,
                                      user_groups=[],
                                      anonUser=True)
            self.assertFalse(self.permisions.has_object_permission(*mocks),
                             mocks)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
