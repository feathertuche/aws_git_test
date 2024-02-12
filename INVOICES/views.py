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
        api_log(msg="Processing GET request in MergeInvoice...")
        merge_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)
        try:
            line_items_data = []
            line_items_payload = request.data.get('line_items', [])
            for line_item_payload in line_items_payload:
                remote_data_payload = line_item_payload.get('remote_data', [])
                remote_data_list = []
                for remote_data_item in remote_data_payload:
                    remote_data_list.append({
                        'invoice_id': remote_data_item.get('invoice_id'),
                        'quantity': remote_data_item.get('quantity'),
                        'total_amount': remote_data_item.get('total_amount')
                    })

                line_item_data = {
                    'id': line_item_payload.get('id'),
                    'remote_id': line_item_payload.get('id'),
                    'name': line_item_payload.get('item'),
                    # 'status': line_item_payload.get('status'),
                    'unit_price': line_item_payload.get('unit_price'),
                    'purchase_price': line_item_payload.get('purchase_price'),
                    'purchase_account': line_item_payload.get('purchase_account'),
                    'sales_account': line_item_payload.get('sales_account'),
                    'company': line_item_payload.get('company'),
                    'remote_updated_at': line_item_payload.get('remote_updated_at'),
                    'remote_was_deleted': line_item_payload.get('remote_was_deleted'),
                    'created_at': line_item_payload.get('created_at'),
                    'modified_at': line_item_payload.get('modified_at'),
                    'account': line_item_payload.get('account'),
                    'remote_data': remote_data_list
                }
                line_items_data.append(line_item_data)

            invoice_request = InvoiceRequest(
                type=request.data.get('model', {}).get('type'),
                contact=request.data.get('model', {}).get('contact'),
                number=request.data.get('number'),  # Assuming number is not nested under 'model'
                line_items=[InvoiceLineItemRequest(**line_item) for line_item in line_items_data]
            )
            response = merge_client.accounting.invoices.create(model=invoice_request)
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



