from LINKTOKEN.model import ErpLinkToken
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
from merge_integration.utils import create_merge_client


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

    def __init__(self, *args, link_token_details=None, **kwargs):
        super().__init__()
        self.org_id = None
        self.entity_id = None

    def get_queryset(self):
        if self.org_id is None or self.entity_id is None:
            return ErpLinkToken.objects.none()
        else:
            filter_token = ErpLinkToken.objects.filter(org_id=self.org_id, entity_id=self.entity_id)
            lnk_token = filter_token.values_list('account_token', flat=1)

        return lnk_token

    def post(self, request, *args, **kwargs):
        api_log(msg="Processing GET request in MergeInvoice...")

        org_id = request.data.get("org_id")
        entity_id = request.data.get("entity_id")

        self.org_id = org_id
        self.entity_id = entity_id

        if self.org_id is None and self.entity_id is None:
            return Response(f"not possible")

        queryset = self.get_queryset()

        if queryset is None:
            # Handle the case where link_token_details is None
            print("link_token_details is None")
            return None

        if len(queryset) == 0:
            # Handle the case where link_token_details is an empty list
            print("link_token_details is an empty list")
            return None

        account_token = queryset[0]
        comp_client = create_merge_client(account_token)

        try:
            line_items_payload = request.data.get('model')
            line_items_data = []
            for line_item_payload in line_items_payload.get('line_items', []):
                line_item_data = {
                    'id': line_item_payload.get('id'),
                    'remote_id': line_item_payload.get('id'),
                    'name': line_item_payload.get('item'),
                    "status": line_item_payload.get('status'),
                    'unit_price': line_item_payload.get('unit_price'),
                    'purchase_price': line_item_payload.get('purchase_price'),
                    'purchase_account': line_item_payload.get('purchase_account'),
                    'sales_account': line_item_payload.get('sales_account'),
                    'currency': line_item_payload.get('currency'),
                    'exchange_rate': line_items_payload.get('exchange_rate'),
                    'remote_updated_at': line_item_payload.get('remote_updated_at'),
                    'remote_was_deleted': line_item_payload.get('remote_was_deleted'),
                    'description': line_item_payload.get('item'),
                    'quantity': line_item_payload.get('quantity'),
                    'created_at': line_item_payload.get('created_at'),
                    'tracking_category': line_item_payload.get('tracking_category'),
                    'tracking_categories': line_item_payload.get('tracking_categories'),
                    'modified_at': line_item_payload.get('modified_at'),
                    'account': line_item_payload.get('account'),
                    'remote_data': line_item_payload.get('remote_data')
                }
                line_items_data.append(line_item_data)
                comp_client.accounting.invoices.create(
                    model=InvoiceRequest(
                        type=line_items_payload.get('type'),
                        due_date=line_items_payload.get('due_date'),
                        contact=line_items_payload.get('contact'),
                        number=line_items_payload.get('number'),
                        memo=line_items_payload.get('memo'),
                        status=line_items_payload.get('status'),
                        company=line_items_payload.get('company'),
                        exchange_rate=line_items_payload.get('exchange_rate'),
                        tracking_categories=line_items_payload.get('tracking_categories'),
                        line_items=[InvoiceLineItemRequest(**line_item) for line_item in line_items_data]))

            return Response({"status": "success", "message": f"Invoice created successfully."},
                            status=status.HTTP_201_CREATED)

        except Exception as e:
            error_message = f"Failed to send data to Kloo API. Error: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
