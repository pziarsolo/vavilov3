from os import remove
from os.path import isfile

from django.db.models.signals import post_delete, pre_save, m2m_changed
from django.dispatch.dispatcher import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from vavilov3.models import ObservationImage
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


@receiver(post_delete, sender=ObservationImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `ObservationImage` object is deleted.
    """
    if instance.image:
        path = instance.image.path
        if isfile(path):
            remove(path)

    if instance.image_medium:
        path = instance.image_small.path
        if isfile(path):
            remove(path)

    if instance.image_small:
        path = instance.image_medium.path
        if isfile(path):
            remove(path)


@receiver(pre_save, sender=ObservationImage)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `ObservationImage` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        new_instance = ObservationImage.objects.get(pk=instance.pk)
        old_image = new_instance.image
    except ObservationImage.DoesNotExist:
        return False

    new_image = instance.image
    if not old_image == new_image:
        paths = [old_image.path]
        paths.append(new_instance.image_medium.path)
        paths.append(new_instance.image_small.path)
        for path in paths:
            if isfile(path):
                remove(path)
