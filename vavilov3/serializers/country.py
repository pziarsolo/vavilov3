from rest_framework import serializers

from vavilov3.serializers.shared import DynamicFieldsModelSerializer
from vavilov3.models import Country


class CountrySerializer(DynamicFieldsModelSerializer):
    stats_by_institute = serializers.SerializerMethodField('_stats_by_institutes')
    stats_by_taxa = serializers.SerializerMethodField('_stats_by_taxa')

    class Meta:
        model = Country
        fields = ('code', 'name', 'num_accessions', 'num_accessionsets',
                  'stats_by_institute', 'stats_by_taxa')

    def _stats_by_institutes(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return obj.stats_by_institute(user)

    def _stats_by_taxa(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return obj.stats_by_taxa(user)
