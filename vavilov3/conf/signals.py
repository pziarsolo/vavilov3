from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from vavilov3.conf.settings import ADMIN_GROUP
User = get_user_model()


@receiver(m2m_changed, sender=User.groups.through)
def manage_staff_by_admin_group(action, instance, **kwargs):
    if action == 'post_add':
        has_admin_group = bool(instance.groups.filter(name=ADMIN_GROUP).count())
        if has_admin_group and not instance.is_staff:
            instance.is_staff = True
    elif action in ('pre_remove',) and kwargs['model'] == Group and kwargs['pk_set']:
        has_admin_group = bool(instance.groups.filter(name=ADMIN_GROUP).count())
        id_ = list(kwargs['pk_set'])
        removed_group_names = Group.objects.filter(id__in=id_).values_list('name', flat=True)
        if has_admin_group and ADMIN_GROUP in removed_group_names:
            instance.is_staff = False
