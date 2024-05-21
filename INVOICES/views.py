import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from INVOICES.helper_functions import (
    filter_invoice_payloads,
    filter_attachment_payloads,
    invoice_patch_payload,
)
from INVOICES.queries import (
    update_erp_id_in_line_items,
    update_invoices_table,
)
from INVOICES.serializers import InvoiceCreateSerializer, InvoiceUpdateSerializer
from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log
from services.merge_service import MergeInvoiceApiService


class InvoiceCreate(APIView):
    """
    API to create invoices in the Merge system.
    """

    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def get_queryset(self):
        """
        Function to query erp_link_token table
        """
        filter_token = ErpLinkToken.objects.filter(id=self.erp_link_token_id)
        lnk_token = filter_token.values_list("account_token", flat=1)

        return lnk_token

    def post(self, request):
        """
        This is an Invoice POST request method
        """
        api_log(msg="Processing GET request in MergeInvoice...")
        data = request.data

        serializer = InvoiceCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.erp_link_token_id = serializer.validated_data.get("erp_link_token_id")
        org_id = serializer.validated_data.get("org_id")

        queryset = self.get_queryset()
        if queryset is None or queryset == []:
            api_log(msg="link_token_details is None or empty")
            return Response(
                "Account token doesn't exist", status=status.HTTP_400_BAD_REQUEST
            )

        try:
            account_token = queryset[0]
            merge_api_service = MergeInvoiceApiService(
                account_token, org_id, self.erp_link_token_id
            )

            api_log(msg=f"Invoice Request : {json.dumps(data)}")
            invoice_data = filter_invoice_payloads(data)
            api_log(msg=f"Invoice Formatted Payload : {invoice_data}")

            invoice_created = merge_api_service.create_invoice(invoice_data)
            if invoice_created is None:
                return Response(
                    {"status": "error", "message": "Failed to create invoice in Merge"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            api_log(msg=f"Merge Invoice Created : {invoice_created}")

            invoice_table_id = invoice_data["id"]
            # erp_invoice_id = invoice_created.model.id
            # erp_remote_id = invoice_created.model.remote_id
            # fetching line items from response body
            invoice_response_line_items = invoice_created.model.line_items
            line_item_list = []
            for loop_line_items in invoice_response_line_items:
                line_item_list.append(loop_line_items)

            # calling function to update remote id as 'erp id' in erp_id field in invoice_line_items table
            update_invoices_table(invoice_table_id, invoice_created.model)
            update_erp_id_in_line_items(invoice_table_id, line_item_list)
            # update_invoices_erp_id(invoice_table_id, erp_invoice_id, erp_remote_id)

            attachment_payload = filter_attachment_payloads(data, invoice_created)
            merge_api_service.create_attachment(attachment_payload)

            return Response(
                {
                    "status": "success",
                    "message": "Invoice and attachment created successfully in Merge",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            error_message = f"EXCEPTION : Failed to create invoice in Merge: {str(e)}"
            return Response(
                {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, invoice_id: str):
        """
        This is an Invoice PATCH request bloc...
        """
        api_log(msg=".....Processing Invoice UPDATE request bloc.....")

        data = request.data
        serializer = InvoiceUpdateSerializer(data=data)
        api_log(msg=f"[SERIALIZER bloc in views file for UPDATE] :: {serializer}")

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.erp_link_token_id = serializer.validated_data.get("erp_link_token_id")
        api_log(msg="1")

        queryset = self.get_queryset()
        org_id = serializer.validated_data.get("org_id")
        if queryset is None or queryset == []:
            api_log(msg="link token details are None or empty")
            return Response(
                "Account token doesn't exist", status=status.HTTP_400_BAD_REQUEST
            )

        try:
            account_token = queryset[0]
            print("THIS IS INVOICE UPDATE view ACCOUNT TOKEN:: ", account_token)
            print("[account token data] ::", account_token)
            merge_api_service = MergeInvoiceApiService(
                account_token, org_id, self.erp_link_token_id
            )
            payload_data = request.data
            api_log(msg=f"payload_data Request : {json.dumps(payload_data)}")
            invoice_data = invoice_patch_payload(payload_data)

            api_log(msg=f"[PAYLOAD FOR INVOICE PATCH view file] : {invoice_data}")
            update_response = merge_api_service.update_invoice(invoice_id, invoice_data)
            api_log(msg=f"PATCH response in views file: {update_response}")

            if update_response is None:
                return Response(
                    {"status": "error", "message": "Failed to create invoice in Merge"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            api_log(msg=f"Merge Invoice Created : {update_response}")

            # line_item_list = []
            # for loop_line_items in update_response["model"]["line_items"]:
            #     api_log(msg=f" loop_line_items: {loop_line_items}")
            #     line_item_list.append(loop_line_items)
            # update_erp_id_in_line_items(invoice_id, line_item_list)

        except Exception as e:
            error_message = f"EXCEPTION : Failed to patch invoice in Merge: {str(e)}"
            api_log(msg=f"{error_message}")
            return Response(
                {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MergeInvoiceCreate(APIView):
    """
    API to create invoices in the kloo Invoices system.
    """

    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def post(self, request):
        """
        Handles POST requests to insert data to the kloo Invoices system.

        Returns:
            Response indicating success or failure of data insertion.
        """

        erp_link_token_id = request.data.get("erp_link_token_id")
        org_id = request.data.get("org_id")

        merge_invoice_api_service = MergeInvoiceApiService(
            self.link_token_details, org_id, erp_link_token_id
        )
        invoice_response = merge_invoice_api_service.get_invoices(self.last_modified_at)

        try:
            if invoice_response["status"]:
                api_log(
                    msg=f"INVOICE : Processing {len(invoice_response['data'])} invoices"
                )

                if len(invoice_response["data"]) == 0:
                    return Response(
                        {
                            "message": "No new data found to insert in the kloo Invoice system"
                        },
                        status=status.HTTP_204_NO_CONTENT,
                    )

                api_log(msg="data inserted successfully in the kloo Invoice system")
                return Response({"message": "API Invoice Info completed successfully"})

            api_log(msg="Failed to send data to Kloo Invoice API")
            return Response(
                {"error": "Failed to send data to Kloo Invoice API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            error_message = f"Failed to send data to Kloo Invoice API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
