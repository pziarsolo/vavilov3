from vavilov3_accession.serializers.shared import DynamicFieldsModelSerializer
from vavilov3_accession.models import DataSource


class DataSourceSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = DataSource
        fields = ('code', 'kind', 'num_passports')
