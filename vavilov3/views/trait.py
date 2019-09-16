from io import TextIOWrapper

from django.core.exceptions import ValidationError

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination,
                                   CheckBeforeRemoveMixim)
from vavilov3.models import Trait, Observation
from vavilov3.permissions import IsAdminOrReadOnly
from vavilov3.serializers.trait import TraitSerializer
from vavilov3.entities.trait import (TraitStruct, parse_obo,
                                     transform_to_trait_entity_format)
from vavilov3.filters.trait import TraitFilter
from vavilov3.views import format_error_message


class TraitViewSet(DynamicFieldsViewMixin, CheckBeforeRemoveMixim,
                   viewsets.ModelViewSet):
    lookup_field = 'name'
    serializer_class = TraitSerializer
    queryset = Trait.objects.all()
    filter_class = TraitFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    Struct = TraitStruct

    @action(methods=['post'], detail=False)
    def create_by_obo(self, request):
        try:
            fhand = TextIOWrapper(request.FILES['obo'].file,
                                  encoding='utf-8')
        except KeyError:
            msg = 'could not found obo file'
            raise ValidationError(format_error_message(msg))

        ontology = parse_obo(fhand)
        data = transform_to_trait_entity_format(ontology)

        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'task_id': serializer.instance.id},
                        status=status.HTTP_200_OK,
                        headers={})

    def check_before_remove(self, instance):
        if Observation.objects.filter(observation_variable__trait=instance).count():
            msg = 'Can not delete this trait because there are observations'
            msg += ' associated with it'
            return Response(format_error_message(msg),
                            status=status.HTTP_400_BAD_REQUEST)
