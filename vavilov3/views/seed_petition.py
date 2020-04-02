'''
Created on 2020(e)ko mar. 23(a)

@author: peio
'''
from vavilov3.views.shared import DynamicFieldsViewMixin
from vavilov3.permissions import SeedPetitionPermission
from vavilov3.models import SeedPetition
from vavilov3.serializers.seed_petition import SeedPetitionSerializer
from rest_framework import viewsets, mixins


class SeedPetitionViewSet(DynamicFieldsViewMixin, mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    queryset = SeedPetition.objects.all().order_by('-petition_date')
    serializer_class = SeedPetitionSerializer
    permission_classes = (SeedPetitionPermission,)
