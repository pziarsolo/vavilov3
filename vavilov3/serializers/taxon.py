from rest_framework import serializers

from vavilov3.serializers.shared import DynamicFieldsModelSerializer
from vavilov3.models import Taxon


class TaxonSerializer(DynamicFieldsModelSerializer):
    rank = serializers.CharField(source='rank.name')

    class Meta:
        model = Taxon
        fields = ['rank', 'name', 'num_accessions', 'num_accessionsets']
