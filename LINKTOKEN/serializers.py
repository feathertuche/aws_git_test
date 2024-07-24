from rest_framework import serializers
from LINKTOKEN.model import ErpLinkToken


class AccountTokenSerializers(serializers.ModelSerializer):
    class Meta:
        model = ErpLinkToken
        fields = ["account_token"]
