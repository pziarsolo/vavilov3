from django.conf import settings

ADMIN_GROUP = getattr(settings, 'VAVILOV3_ADMIN_GROUP', 'admin')
