from rest_framework import serializers


class ProxyReSyncSerializer(serializers.Serializer):
    org_id = serializers.UUIDField()
    entity_id = serializers.UUIDField()
    erp_link_token_id = serializers.UUIDField()
