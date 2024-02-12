from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration import settings
from merge.client import Merge
from merge.resources.accounting import (
    InvoicesListRequestExpand, InvoicesListRequestType, \
    InvoiceLineItemRequest, InvoiceRequest
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
                type=InvoicesListRequestType.ACCOUNTS_PAYABLE,
            )
        except Exception as e:
            api_log(
                msg=f"Error retrieving invoices details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
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


class MergeInvoiceCreate(APIView):
    def post(self, request, *args, **kwargs):
        request.data
        api_log(msg="Processing GET request in MergeInvoice...")
        merge_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)
        try:
            response = merge_client.accounting.invoices.create(model=InvoiceRequest(
                type=request.data.get('type'),
                contact=request.data.get('contact'),
                line_items=[
                    InvoiceLineItemRequest(
                        id=request.data.get('id'),
                        remote_id=request.data.get('remote_id'),
                        name=request.data.get('name'),
                        status=request.data.get('status'),
                        unit_price=request.data.get('unit_price'),
                        purchase_price=request.data.get('purchase_price'),
                        purchase_account=request.data.get('purchase_account'),
                        sales_account=request.data.get('sales_account'),
                        company=request.data.get('company'),
                        remote_updated_at=request.data.get('remote_updated_at'),
                        remote_was_deleted=request.data.get('remote_was_deleted'),
                        created_at=request.data.get('created_at'),
                        modified_at=request.data.get('modified_at'),
                        account=request.data.get('account'),
                        remote_data=None
                    )
                ]
            )
            )

            if not response.errors:
                api_log(msg="Invoice created successfully.")
                return Response({"status": "success", "message": f"Invoice created successfully.{response.model}"},
                                status=status.HTTP_201_CREATED)

            else:
                error_message = f"Failed to create invoice. Status code: {response.logs}"
                api_log(msg=error_message)
                return Response({"status": "error", "message": error_message},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            error_message = f"An error occurred while creating invoice: {str(e)}"
            api_log(msg=error_message)
            return Response({"status": "error", "message": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
