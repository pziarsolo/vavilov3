from django_filters import rest_framework as filters

from vavilov3.models import Scale
from vavilov3.filters.shared import TermFilterMixin


class ScaleFilter(TermFilterMixin, filters.FilterSet):

    class Meta:
        model = Scale
        fields = {'name': ['exact', 'iexact', 'icontains']}
