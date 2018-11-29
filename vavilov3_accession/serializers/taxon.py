from rest_framework import serializers

from vavilov3_accession.serializers.shared import DynamicFieldsModelSerializer
from vavilov3_accession.models import Taxon


class TaxonSerializer(DynamicFieldsModelSerializer):
    rank = serializers.CharField(source='rank.name')

    class Meta:
        model = Taxon
        fields = ['rank', 'name', 'num_accessions', 'num_accessionsets']
