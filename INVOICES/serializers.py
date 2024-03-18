from rest_framework import serializers
from rest_framework.fields import ListField


class AttachmentSerializer(serializers.Serializer):
    file_name = serializers.CharField()
    file_url = serializers.URLField()
    transaction_name = serializers.CharField()


class ModelSerializer(serializers.Serializer):
    line_items = ListField()
    attachment = AttachmentSerializer()


class InvoiceCreateSerializer(serializers.Serializer):
    erp_link_token_id = serializers.CharField()
    model = ModelSerializer()
