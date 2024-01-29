from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration import settings
from merge.client import Merge
from merge.resources.accounting import (
    InvoicesListRequestExpand,
)
import traceback
from merge_integration.helper_functions import api_log


class MergeInvoices(APIView):
    @staticmethod
    def get(_):
        api_log(msg="Processing GET request in MergeAccounts...")
        merge_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)
        try:
            invoice_data = merge_client.accounting.invoices.list(
                expand=InvoicesListRequestExpand.ACCOUNTING_PERIOD,
                remote_fields="type",
                show_enum_origins="type",
                #type=InvoicesListRequestType.ACCOUNTS_PAYABLE,
            )
        except Exception as e:
            api_log(msg=f"Error retrieving invoices details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        formatted_data = []
        for account in invoice_data.results:
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

        api_log(msg=f"FORMATTED DATA: {formatted_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_data, status=status.HTTP_200_OK)