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
            response = merge_client.accounting.invoices.create(model=InvoiceRequest(
                type="ACCOUNTS_RECEIVABLE",
                contact="fb9ab654-67d5-43ba-870c-95ab566781f8",
                line_items=[
                    InvoiceLineItemRequest(
                        id="c926f339-1531-4c8b-8f29-a67c475041b2",
                        remote_id="TSM - Black",
                        name="T-Shirt Medium Black",
                        # description= "Pickleball lessons",
                        # quantity=1,
                        status=None,
                        unit_price=40.0,
                       # total_amount=50,
                        # currency="USD",
                        #exchange_rate="2.9",
                        purchase_price=20.0,
                        purchase_account=None,
                        sales_account="707cf8b3-e2b4-471e-bd45-d2bcf1af3bd1",
                        company=None,
                        remote_updated_at="2024-01-15T07:43:26.363000Z",
                        remote_was_deleted=False,
                        created_at="2024-01-16T06:48:02.878806Z",
                        modified_at="2024-01-16T06:48:02.878811Z",
                        account="67df4fa6-f282-4734-aa9b-1cb37a44e46c",
                        remote_data=None
                    )
                ]
            )
            )
            print("@@@@@@@@@@@@@", response.errors)

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
