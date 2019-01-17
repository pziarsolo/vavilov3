import unittest

from unittest.mock import MagicMock

from django.contrib.auth.models import AnonymousUser

from vavilov3.permissions import UserGroupObjectPublicPermission


class PermissionsTest(unittest.TestCase):

    def setUp(self):
        self.permisions = UserGroupObjectPublicPermission()

    @staticmethod
    def set_up_mocks(obj_owner, obj_is_public, action, user_is_staff,
                     user_groups=[], anonUser=False):
        obj = MagicMock(owner=obj_owner, is_public=obj_is_public)
        request = MagicMock(user=MagicMock(is_staff=user_is_staff,
                                           token={'groups': user_groups}))
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
            if action == 'partial_update':
                self.assertFalse(self.permisions.has_object_permission(*mocks),
                                 mocks)
            else:
                self.assertTrue(self.permisions.has_object_permission(*mocks),
                                mocks)

        # if it is yours and is public, allow anything
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
