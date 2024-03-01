from rest_framework import serializers
from rest_framework.fields import ListField


class AttachmentSerializer(serializers.Serializer):
    file_name = serializers.CharField()
    file_url = serializers.URLField()
    integration_params = serializers.DictField(child=serializers.CharField())


class ModelSerializer(serializers.Serializer):
    line_items = ListField()
    attachment = AttachmentSerializer()


class InvoiceCreateSerializer(serializers.Serializer):
    org_id = serializers.UUIDField()
    model = ModelSerializer()
