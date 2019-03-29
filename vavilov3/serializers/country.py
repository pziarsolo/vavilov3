from rest_framework import serializers

from vavilov3.models import Country


class CountrySerializer(serializers.ModelSerializer):
    stats_by_institute = serializers.SerializerMethodField('_stats_by_institutes')
    stats_by_taxa = serializers.SerializerMethodField('_stats_by_taxa')

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        # Instantiate the superclass normally
        super(serializers.ModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        else:
            self.fields.pop('stats_by_institute')
            self.fields.pop('stats_by_taxa')

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
