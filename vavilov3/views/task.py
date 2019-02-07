import json
import time

from django.contrib.auth.models import AnonymousUser

from rest_framework import viewsets, status, serializers
from rest_framework.response import Response

from django_celery_results.models import TaskResult

from vavilov3_web.celeryapp import app
from vavilov3.views import format_error_message
from vavilov3.models import UserTasks
from vavilov3.permissions import is_user_admin


class TaskResultSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    status = serializers.CharField()
    name = serializers.CharField()


class TaskDoesNotExistError(Exception):
    pass


class TaskResultGetter():

    def __init__(self, task_id):
        self._data = {}
        try:
            db_result = TaskResult.objects.get(task_id=task_id)
        except TaskResult.DoesNotExist:
            db_result = None
        self._db_result = db_result

        active_task = None
        if self._db_result is None:
            active_tasks_by_id = get_active_tasks()
            try:
                active_task = active_tasks_by_id[task_id]
            except KeyError:
                pass

        try:
            user_task = UserTasks.objects.get(task_id=task_id)
        except UserTasks.DoesNotExist:
            user_task = None
        self._user_task = user_task
        self._active_task = active_task
        if self._user_task:
            self.username = self._user_task.user.username
        else:
            self.username = None

        if self._active_task is None and db_result is None:
            raise TaskDoesNotExistError()
        elif self._active_task and not db_result:
            self.status = 'PENDING'
            self.task_name = self._active_task['name']
            self.result = {}
        elif db_result:
            self.status = db_result.status
            self.task_name = db_result.task_name
            self.result = db_result.result
            self.date_done = db_result.date_done
        self.task_id = task_id

#         print('django')
#         print(db_result.date_done)
#         print(dir(db_result))
#         print(dir(active_task))
# #         print(async_result._get_task_meta())
#         pprint('rabbit')
#         pprint(async_result)

    @staticmethod
    def exists(async_result):
        if async_result._get_task_meta()['task_name'] is not None:
            return True
        return False

    @property
    def status(self):
        return self._data['status']

    @status.setter
    def status(self, status):
        self._data['status'] = status

    @property
    def task_id(self):
        return self._data['task_id']

    @task_id.setter
    def task_id(self, task_id):
        self._data['task_id'] = task_id

    @property
    def task_name(self):
        return self._data['task_name']

    @task_name.setter
    def task_name(self, task_name):
        self._data['task_name'] = task_name

    @property
    def result(self):
        if self.status == 'PENDING':
            result = ''
        elif self.status == 'FAILURE':
            result = json.loads(self._data['result'])["exc_message"][0]
        elif self.status == 'SUCCESS':
            result = json.loads(self._data['result'])['detail']

        return result

    @result.setter
    def result(self, result):
        self._data['result'] = result

    @property
    def name(self):
        try:
            return self.task_name.split('.')[-1].replace('_', ' ').title()
        except AttributeError:
            return None

    @property
    def username(self):
        return self._data['username']

    @username.setter
    def username(self, username):
        self._data['username'] = username

    @property
    def date_done(self):
        return self._data.get('date_done', None)

    @date_done.setter
    def date_done(self, date_done):
        self._data['date_done'] = date_done

    @property
    def data(self):
        return {'task_id': self.task_id,
                'task_name': self.task_name,
                'name': self.name,
                'status': self.status,
                'result': self.result,
                'owner': self.username,
                'date_done': self.date_done}

    def delete(self):
        if self._active_task:
            self._active_task.forget()
        if self._db_result:
            self._db_result.delete()
        if self._user_task:
            self._user_task.delete()


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
        active_tasks_by_ids = get_active_tasks()
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


def get_active_tasks():
    inspect = app.control.inspect()
    active_tasks_by_id = {}

    try:
        active_tasks = inspect.active()
    except ConnectionResetError:
        time.sleep(0.2)
        active_tasks = inspect.active()

    try:
        active_tasks_by_queue = active_tasks.values()
    except AttributeError:
        time.sleep(0.2)
        active_tasks_by_queue = active_tasks.values()

    for tasks_in_queue in active_tasks_by_queue:
        for task in tasks_in_queue:
            active_tasks_by_id[task['id']] = task
    return active_tasks_by_id
