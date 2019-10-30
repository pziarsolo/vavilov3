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

from django.contrib.auth.models import AnonymousUser

from rest_framework import viewsets, status
from rest_framework.response import Response

from django_celery_results.models import TaskResult

from vavilov3.views import format_error_message
from vavilov3.models import UserTasks
from vavilov3.permissions import is_user_admin
from vavilov3.entities.task_result_getter import (TaskResultGetter,
                                                  TaskDoesNotExistError,
                                                  get_active_tasks)


class TaskViewSet(viewsets.ViewSet):
    lookup_field = 'task_id'

    @staticmethod
    def filter_by_permission(task_ids, user):

        if isinstance(user, AnonymousUser):
            return []
        elif is_user_admin(user):
            return task_ids
        else:
            queryset = UserTasks.objects.filter(user=user, task_id__in=task_ids)
            return queryset.values_list('task_id', flat=True)

    def retrieve(self, request, task_id):
        try:
            task_id = self.filter_by_permission([task_id], user=request.user)[0]
        except IndexError:
            return Response(format_error_message('Task does not exists'),
                            status=status.HTTP_404_NOT_FOUND)
        try:
            task = TaskResultGetter(task_id)
        except TaskDoesNotExistError:
            return Response(format_error_message('Task does not exists'),
                            status=status.HTTP_404_NOT_FOUND)

        return Response(task.data, status=status.HTTP_200_OK)

    def delete(self, request, task_id):
        try:
            task_id = self.filter_by_permission([task_id], user=request.user)[0]
        except IndexError:
            return Response(format_error_message('You dont have permissions'),
                            status=status.HTTP_403_FORBIDDEN)

        task = TaskResultGetter(task_id)
        task.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        try:
            active_tasks_by_ids = get_active_tasks()
        except ValueError:
            active_tasks_by_ids = {}
        task_ids = []

        task_ids.extend(active_tasks_by_ids.keys())
        for task_result in TaskResult.objects.all():
            task_ids.append(task_result.task_id)

        task_ids = self.filter_by_permission(task_ids, user=request.user)
        tasks = []
        for task_id in task_ids:
            try:
                task = TaskResultGetter(task_id)
            except TaskDoesNotExistError:
                task = None
            if task:
                tasks.append(task)

        return Response([task.data for task in tasks],
                        status=status.HTTP_200_OK)
