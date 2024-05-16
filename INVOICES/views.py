import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from INVOICES.helper_functions import (
    filter_invoice_payloads,
    filter_attachment_payloads,
)
from INVOICES.queries import (
    update_invoices_erp_id,
    update_erp_id_in_line_items,
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
            erp_invoice_id = invoice_created.model.id
            erp_remote_id = invoice_created.model.remote_id
            # fetching line items from response body
            invoice_response_line_items = invoice_created.model.line_items
            line_item_list = []
            for loop_line_items in invoice_response_line_items:
                line_item_list.append(loop_line_items)

            # calling function to update remote id as 'erp id' in erp_id field in invoice_line_items table
            update_erp_id_in_line_items(invoice_table_id, line_item_list)
            update_invoices_erp_id(invoice_table_id, erp_invoice_id, erp_remote_id)

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
            line_items = []
            for line_item_data in payload_data["model"]["line_items"]:
                line_item = {
                    "id": line_item_data.get("id"),
                    "remote_id": line_item_data.get("remote_id"),
                    "unit_price": float(
                        line_item_data.get("unit_price")
                        if line_item_data.get("unit_price") is not None
                        else 0
                    ),
                    "currency": line_item_data.get("currency"),
                    "exchange_rate": line_item_data.get("exchange_rate"),
                    "remote_was_deleted": line_item_data.get("remote_was_deleted"),
                    "description": line_item_data.get("item"),
                    "quantity": float(
                        line_item_data.get("quantity")
                        if line_item_data.get("quantity") is not None
                        else 0
                    ),
                    "created_at": line_item_data.get("created_at"),
                    "tracking_categories": line_item_data.get("tracking_categories"),
                    # "integration_params": {
                    #     "tax_rate_remote_id": line_item_data.get("tax_rate_remote_id")
                    # },
                    "account": line_item_data.get("account"),
                    "remote_data": line_item_data.get("remote_data"),
                }
                line_items.append(line_item)

            payload = {
                "model": {
                    "id": invoice_id,
                    "remote_id": payload_data["model"].get("remote_id"),
                    "type": payload_data["model"].get("type"),
                    "due_date": payload_data["model"].get("due_date"),
                    "issue_date": payload_data["model"].get("issue_date"),
                    "contact": payload_data["model"].get("contact"),
                    "number": payload_data["model"].get("number"),
                    "memo": payload_data["model"].get("memo"),
                    "status": payload_data["model"].get("status"),
                    "company": payload_data["model"].get("company"),
                    "currency": payload_data["model"].get("currency"),
                    "tracking_categories": payload_data["model"].get(
                        "tracking_categories"
                    ),
                    "sub_total": float(
                        payload_data["model"].get("sub_total")
                        if payload_data["model"].get("sub_total") is not None
                        else 0
                    ),
                    "total_tax_amount": float(
                        payload_data["model"].get("total_tax_amount")
                        if payload_data["model"].get("total_tax_amount") is not None
                        else 0
                    ),
                    "total_amount": float(
                        payload_data["model"].get("total_amount")
                        if payload_data["model"].get("total_amount") is not None
                        else 0
                    ),
                    "line_items": line_items,
                },
                "warnings": [],
                "errors": [],
            }

            api_log(msg=f"[PAYLOAD FOR INVOICE PATCH view file] : {payload}")
            update_response = merge_api_service.update_invoice(invoice_id, payload)
            api_log(msg=f"PATCH response in views file: {update_response}")

            if update_response is not None:
                api_log(msg="7")
                return Response(
                    {
                        "status": "success",
                        "message": "successfully update invoice in Merge",
                        "response_data": update_response,
                    },
                    status=status.HTTP_200_OK,
                )

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
