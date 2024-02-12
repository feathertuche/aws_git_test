from rest_framework import serializers
from COMPANY_INFO.models import ErpLinkToken


class AccountTokenSerializers(serializers.ModelSerializer):
    class Meta:
        model = ErpLinkToken
        fields = ['account_token']