from rest_framework import viewsets
from vavilov3_accession.models import Accession
from vavilov3_accession.views.shared import (DynamicFieldsViewMixin,
                                             StandardResultsSetPagination,
                                             MultipleFieldLookupMixin)
from vavilov3_accession.serializers.accession import AccessionSerializer
from vavilov3_accession.filters.accession import AccessionFilter


class AccessionViewSet(MultipleFieldLookupMixin, DynamicFieldsViewMixin,
                       viewsets.ModelViewSet):
    lookup_fields = ('institute_code', 'germplasm_number')
    lookup_url_kwarg = 'institute_code>[^/]+):(?P<germplasm_number'
    lookup_value_regex = '[^/]+'
    filter_foreignkey_mapping = {'institute_code': 'institute__code'}
    queryset = Accession.objects.all()
    serializer_class = AccessionSerializer
    filter_class = AccessionFilter
#     permission_classes = (IsAdminOrReadOnly,)

    pagination_class = StandardResultsSetPagination
