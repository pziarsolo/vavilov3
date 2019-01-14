from django.db import connection

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from vavilov3.models import Taxon
from vavilov3.views.shared import (MultipleFieldLookupMixin,
                                   StandardResultsSetPagination)
from vavilov3.serializers.taxon import TaxonSerializer
from vavilov3.filters.taxon import TaxonFilter
from vavilov3.raw_stat_sql_commands import get_taxa_stas_raw_sql


class TaxonViewSet(MultipleFieldLookupMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Taxon.objects
    serializer_class = TaxonSerializer
    filter_class = TaxonFilter
    lookup_fields = ('rank', 'name')
    filter_foreignkey_mapping = {'rank': 'rank__name', 'name': 'name'}
    lookup_url_kwarg = 'rank>[^/.]+)/(?P<name'
    pagination_class = StandardResultsSetPagination

    @action(methods=['GET'], detail=False)
    def stats_by_rank(self, request, *args, **kwargs):
        stats = {}
#         for accession_stat in Taxon.objects.raw(get_taxa_stas_raw_sql('accession')):
#             print(accession_stat)
        with connection.cursor() as cursor:
            cursor.execute(get_taxa_stas_raw_sql('accession', request.user))
            for taxon_stat in cursor.fetchall():
                name = taxon_stat[1]
                rank = taxon_stat[2]
                num_accessions = taxon_stat[3]
                if num_accessions != 0:
                    if rank not in stats:
                        stats[rank] = {}
                    stats[rank][name] = {
                        'num_accessions': num_accessions,
                        'num_accessionsets': 0}
        with connection.cursor() as cursor:
            cursor.execute(get_taxa_stas_raw_sql('accessionset', request.user))
            for taxon_stat in cursor.fetchall():
                name = taxon_stat[1]
                rank = taxon_stat[2]
                num_accessionsets = taxon_stat[3]
                if num_accessions != 0:
                    if rank not in stats:
                        stats[rank] = {}
                    if name in stats[rank]:
                        stats[rank][name]['num_accessionsets'] = num_accessionsets
                    else:
                        stats[rank][name] = {
                            'num_accessions': 0,
                            'num_accessionsets': num_accessionsets}
        return Response(stats)
#                 num_accessionsets = taxon_stat[4]
#                 if (num_accessions != 0 or num_accessionsets != 0):
#                     if rank not in stats:
#                         stats[rank] = {}
#                 stats[rank][name] = {
#                     'num_accessions': num_accessions,
#                     'num_accessionsets': num_accessionsets}
#         return Response(stats)

#         serializer = self.get_serializer(self.queryset, many=True)
#         serialized_data = serializer.data
#         stats = {}
#         for taxon_data in serialized_data:
#             if (taxon_data['num_accessions'] != 0 or
#                     taxon_data['num_accessionsets'] != 0):
#                 if taxon_data['rank'] not in stats:
#                     stats[taxon_data['rank']] = {}
#                 stats[taxon_data['rank']][taxon_data['name']] = {
#                     'num_accessions': taxon_data['num_accessions'],
#                     'num_accessionsets': taxon_data['num_accessionsets']}
#         return Response(stats)
