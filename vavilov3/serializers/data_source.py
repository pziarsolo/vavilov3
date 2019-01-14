from vavilov3.serializers.shared import DynamicFieldsModelSerializer
from vavilov3.models import DataSource


class DataSourceSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = DataSource
        fields = ('code', 'kind', 'num_passports')
