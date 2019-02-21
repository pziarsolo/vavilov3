
from rest_framework import viewsets

from vavilov3.views.shared import (DynamicFieldsViewMixin,
                                   StandardResultsSetPagination)
from vavilov3.models import Trait
from vavilov3.permissions import IsAdminOrReadOnly

from vavilov3.serializers.trait import TraitSerializer
from vavilov3.entities.trait import TraitStruct
from vavilov3.filters.trait import TraitFilter


class TraitViewSet(DynamicFieldsViewMixin, viewsets.ModelViewSet):
    lookup_field = 'name'
    serializer_class = TraitSerializer
    queryset = Trait.objects.all()
    filter_class = TraitFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    Struct = TraitStruct
