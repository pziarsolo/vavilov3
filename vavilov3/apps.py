from django.apps import AppConfig


class Vavilov3Config(AppConfig):
    name = 'vavilov3'

    def ready(self):
        from vavilov3.conf import signals
