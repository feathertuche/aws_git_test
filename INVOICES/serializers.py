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


class InvoiceUpdateSerializer(serializers.Serializer):
    erp_link_token_id = serializers.CharField()
    model = serializers.DictField()


class ErpInvoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    organization_id = serializers.UUIDField(required=False, allow_null=True)
    erp_link_token_id = serializers.UUIDField(required=False, allow_null=True)
    type = serializers.CharField(required=False, allow_null=True)
    contact = serializers.UUIDField(required=False, allow_null=True)
    number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    issue_date = serializers.DateTimeField(required=False, allow_null=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    paid_on_date = serializers.DateTimeField(required=False, allow_null=True)
    memo = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    company = serializers.CharField(required=False, allow_null=True)
    currency = serializers.UUIDField(required=False, allow_null=True)
    exchange_rate = serializers.CharField(required=False, allow_null=True)
    total_discount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    sub_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    erp_status = serializers.CharField(required=False, allow_null=True)
    total_tax_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    tracking_categories = serializers.ListField(required=False, allow_null=True)
    payments = serializers.ListField(required=False, allow_null=True)
    applied_payments = serializers.ListField(required=False, allow_null=True)
    line_items = serializers.ListField(required=False, allow_null=True)
    accounting_period = serializers.CharField(required=False, allow_null=True)
    purchase_orders = serializers.ListField(required=False, allow_null=True)
    erp_created_at = serializers.DateTimeField(required=False, allow_null=True)
    erp_modified_at = serializers.DateTimeField(required=False, allow_null=True)
    erp_field_mappings = serializers.JSONField(required=False, allow_null=True)
    erp_remote_data = serializers.JSONField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
