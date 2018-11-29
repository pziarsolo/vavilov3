from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from vavilov3_accession.models import Taxon
from vavilov3_accession.views.shared import MultipleFieldLookupMixin
from vavilov3_accession.serializers.taxon import TaxonSerializer
from vavilov3_accession.filters.taxon import TaxonFilter


class TaxonViewSet(MultipleFieldLookupMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Taxon.objects
    serializer_class = TaxonSerializer
    filter_class = TaxonFilter
    lookup_fields = ('rank', 'name')
    filter_foreignkey_mapping = {'rank': 'rank__name', 'name': 'name'}
    lookup_url_kwarg = 'rank>[^/.]+)/(?P<name'

    @action(methods=['GET'], detail=False)
    def stats_by_rank(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.queryset, many=True)
        serialized_data = serializer.data
        stats = {}
        for taxon_data in serialized_data:
            if (taxon_data['num_accessions'] != 0 or
                    taxon_data['num_accessionsets'] != 0):
                if taxon_data['rank'] not in stats:
                    stats[taxon_data['rank']] = {}
                stats[taxon_data['rank']][taxon_data['name']] = {
                    'num_accessions': taxon_data['num_accessions'],
                    'num_accessionsets': taxon_data['num_accessionsets']}
        import pprint
        pprint.pprint(stats)
        return Response(stats)
