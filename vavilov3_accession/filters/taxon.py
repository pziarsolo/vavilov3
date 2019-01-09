from django_filters import rest_framework as filters

from vavilov3_accession.models import Taxon


class TaxonFilter(filters.FilterSet):

    class Meta:
        model = Taxon
        fields = {'name': ['icontains']}