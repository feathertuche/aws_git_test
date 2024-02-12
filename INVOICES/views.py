import sys

from django.http import HttpResponse
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
        line_items_payload = request.data.get('model')
        line_items_data = []
        for line_item_payload in line_items_payload.get('line_items', []):
            line_item_data = {
                'id': line_item_payload.get('id'),
                'remote_id': line_item_payload.get('id'),
                'name': line_item_payload.get('item'),
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
                'remote_data': None
            }
            # Append each line_item_data to line_items_data within the loop
            line_items_data.append(line_item_data)
            # Use the populated line_items_data list to create the invoice
        merge_client.accounting.invoices.create(
            model=InvoiceRequest(
                type=line_items_payload.get('type'),
                contact=line_items_payload.get('contact'),
                number=line_items_payload.get('number'),
                line_items=[
                    InvoiceLineItemRequest(**line_item) for line_item in line_items_data
                ],
            ),
        )
        return Response({"status": "success", "message": f"Invoice created successfully."},
                        status=status.HTTP_201_CREATED)



            # response = merge_client.accounting.invoices.create(model=invoice_request)
            # if not response.errors:
            #     api_log(msg="Invoice created successfully.")
            #     return Response({"status": "success", "message": f"Invoice created successfully.{response.model}"},
            #                     status=status.HTTP_201_CREATED)




