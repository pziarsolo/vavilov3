from django.conf import settings

ADMIN_GROUP = getattr(settings, 'VAVILOV3_ADMIN_GROUP', 'admin')

ALLOWED_TAXONOMIC_RANKS = ['family', 'genus', 'species', 'subspecies',
                           'variety', 'convarietas', 'group', 'forma']
USERS_CAN_CREATE_ACCESSIONSETS = getattr(
    settings, 'VAVILOV3_USERS_CAN_CREATE_ACCESSIONSETS', 'admin')
