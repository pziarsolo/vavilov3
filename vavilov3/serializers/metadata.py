from rest_framework import serializers


class MetadataSerializer(serializers.Serializer):
    group = serializers.CharField()
    is_public = serializers.BooleanField()
