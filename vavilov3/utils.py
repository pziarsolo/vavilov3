import os
from django.conf import settings
from vavilov3.models import ObservationImage


def observation_image_cleanup(delete=False):
    physical_files = set()
    db_files = set()

    # Get all files from the database
    for field in ['image', 'image_medium', 'image_small']:
        files = ObservationImage.objects.all().values_list(field, flat=True)
        db_files.update(files)

    # Get all files from the MEDIA_ROOT, recursively
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if media_root is not None:
        for relative_root, dirs, files in os.walk(media_root):
            for file_ in files:
                # Compute the relative file path to the media directory, so it can be compared to the values from the db
                relative_file = os.path.join(os.path.relpath(relative_root, media_root), file_)
                physical_files.add(relative_file)

    # Compute the difference and delete those files
    deletables = physical_files - db_files
    if deletables:
        for file_ in deletables:
            if delete:
                os.remove(os.path.join(media_root, file_))
            else:
                print(os.path.join(media_root, file_))
            #

        # Bottom-up - delete all empty folders
        for relative_root, dirs, files in os.walk(media_root, topdown=False):
            for dir_ in dirs:
                if not os.listdir(os.path.join(relative_root, dir_)):
                    if delete:
                        os.rmdir(os.path.join(relative_root, dir_))
                    else:
                        print(os.path.join(relative_root, dir_))
                    # os.rmdir(os.path.join(relative_root, dir_))
