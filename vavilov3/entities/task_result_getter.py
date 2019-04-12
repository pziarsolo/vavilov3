import json
import time

from celery.app import app_or_default

from django_celery_results.models import TaskResult

from vavilov3.models import UserTasks


class TaskDoesNotExistError(Exception):
    pass


POLLING_STEP = 0.2
TIMEOUT_LIMIT = 1


def task_in_active_tasks(active_tasks, task_id):
    for tasks in active_tasks.values():
        for task in tasks:
            if task_id == task['id']:
                return True
    return False


def get_active_tasks(task_id=None):
    app = app_or_default()
    inspect = app.control.inspect()
    active_tasks_by_id = {}
    active_tasks = None
    time_counter = 0
    while True:
        try:
            active_tasks = inspect.active()
        except ConnectionResetError:
            pass
        time.sleep(POLLING_STEP)
        time_counter += POLLING_STEP
        if time_counter > TIMEOUT_LIMIT:
            raise ValueError('Can not get active tasks')
        if (active_tasks is not None):
            if (task_id is None and len(active_tasks.values()) > 0):
                break
            elif (task_id is not None and task_in_active_tasks(active_tasks, task_id)):
                break

    active_tasks_by_queue = None
    time_counter = 0
    while not active_tasks_by_queue:
        try:
            active_tasks_by_queue = active_tasks.values()
        except AttributeError:
            pass

        time.sleep(POLLING_STEP)
        time_counter += POLLING_STEP
#         print(time_counter)
        if time_counter > TIMEOUT_LIMIT:
            raise ValueError('Can not get active tasks')

    for tasks_in_queue in active_tasks_by_queue:
        for task in tasks_in_queue:
            active_tasks_by_id[task['id']] = task

    return active_tasks_by_id


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
            try:
                active_tasks_by_id = get_active_tasks(task_id)
            except ValueError:
                active_tasks_by_id = {}
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
            result = json.loads(self._data['result'])
            if 'detail' in result:
                return result['detail']
            return "Internal Job successful"
        elif self.status == 'REVOKED':
            result = ''

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
        app = app_or_default()
        if self._active_task:
            app.control.revoke(self._active_task['id'], terminate=True)
#             self._active_task.forget()
        if self._db_result:
            self._db_result.delete()
        if self._user_task:
            self._user_task.delete()
