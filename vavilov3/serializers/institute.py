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

from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError

from vavilov3.serializers.shared import DynamicFieldsSerializer
from vavilov3.entities.institute import (InstituteStruct,
                                         InstituteValidationError,
                                         validate_institute_data,
                                         create_institute_in_db,
                                         update_institute_in_db)
from vavilov3.views import format_error_message
from vavilov3.tasks import create_institutes_task, wait_func, add_task_to_user


class InstituteListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        if user is None:
            error = 'User must be logged'
            raise ValidationError(format_error_message(error))

        if not user.groups.exists():
            error = 'User must belong to a group'
            raise ValidationError(format_error_message(error))

        async_result = create_institutes_task.delay(validated_data)
#         async_result = wait_func.delay(5)
        add_task_to_user(user, async_result)
        return async_result

    def update(self, instance, validated_data):
        instances = []
        errors = []
        with transaction.atomic():
            for instance, payload in zip(instance, validated_data):
                try:
                    instances.append(update_institute_in_db(payload, instance))
                except ValueError as error:
                    errors.append(error)
                except IntegrityError as error:
                    errors.append(error)

            if errors:
                raise ValidationError(format_error_message(errors))
            else:
                return instances


class InstituteSerializer(DynamicFieldsSerializer):
    code = serializers.CharField()
    name = serializers.CharField()

    class Meta:
        list_serializer_class = InstituteListSerializer

    def to_representation(self, instance):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        institute_struct = InstituteStruct(instance=instance,
                                           fields=self.selected_fields,
                                           user=user)
        return institute_struct.get_api_document()

    def run_validation(self, data=empty):
        try:
            validate_institute_data(data)
        except InstituteValidationError as error:
            raise ValidationError(format_error_message(error))
        return data

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        if user is None:
            error = 'User must be logged'
            raise ValidationError(format_error_message(error))

        if not user.groups.exists():
            error = 'User must belong to a group'
            raise ValidationError(format_error_message(error))
        try:
            return create_institute_in_db(validated_data)
        except ValueError as error:
            raise ValidationError(format_error_message(error))
        except IntegrityError as error:
            raise ValidationError(format_error_message(error))

    def update(self, instance, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        if user is None:
            error = 'User must be logged'
            raise ValidationError(format_error_message(error))

        if not user.groups.exists():
            error = 'User must belong to a group'
            raise ValidationError(format_error_message(error))
        try:
            return update_institute_in_db(validated_data, instance)
        except ValueError as error:
            raise ValidationError(format_error_message(error))
