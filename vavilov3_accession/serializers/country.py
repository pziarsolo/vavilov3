from vavilov3_accession.serializers.shared import DynamicFieldsModelSerializer
from vavilov3_accession.models import Country


class CountrySerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Country
        fields = ('code', 'name', 'num_accessions')
