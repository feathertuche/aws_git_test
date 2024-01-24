from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration import settings
from merge.client import Merge
from merge.resources.accounting import (
    AccountsListRequestRemoteFields,
    AccountsListRequestShowEnumOrigins,
)


class MergeAccounts(APIView):
    @staticmethod
    def get(_):
        merge_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)
        try:
            accounts_data = merge_client.accounting.accounts.list(
                expand="company",
                remote_fields=AccountsListRequestRemoteFields.CLASSIFICATION,
                show_enum_origins=AccountsListRequestShowEnumOrigins.CLASSIFICATION,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        formatted_data = []
        for account in accounts_data.results:
            formatted_entry = {
                'id': account.id,
                'remote_id': account.remote_id,
                'name': account.name,
                'description': account.description,
                'classification': account.classification,
                'type': account.type,
                'status': account.status,
                'account_number': account.account_number
            }
            formatted_data.append(formatted_entry)

        return Response(formatted_data, status=status.HTTP_200_OK)