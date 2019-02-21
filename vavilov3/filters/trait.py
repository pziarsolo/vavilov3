from django_filters import rest_framework as filters

from vavilov3.models import Trait
from vavilov3.filters.shared import TermFilterMixin


class TraitFilter(TermFilterMixin, filters.FilterSet):

    class Meta:
        model = Trait
        fields = {'name': ['exact', 'iexact', 'icontains']}
