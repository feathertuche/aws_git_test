from merge.resources.accounting import (
    InvoiceLineItemRequest,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from INVOICES.helper_functions import format_merge_invoice_data
from INVOICES.queries import update_invoices_erp_id
from INVOICES.serializers import InvoiceCreateSerializer, InvoiceUpdateSerializer, ErpInvoiceSerializer
from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log
from services.kloo_service import KlooService
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
        filter_token = ErpLinkToken.objects.filter(id=self.erp_link_token_id)
        lnk_token = filter_token.values_list("account_token", flat=1)

        return lnk_token

    def post(self, request):
        api_log(msg="Processing GET request in MergeInvoice...")
        data = request.data

        # Validate the request data
        serializer = InvoiceCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get the erp_link_token_id from the request data
        self.erp_link_token_id = serializer.validated_data.get("erp_link_token_id")

        queryset = self.get_queryset()
        if queryset is None or queryset == []:
            # Handle the case where link_token_details is None
            api_log(msg="link_token_details is None or empty")
            return Response(
                "Account token doesn't exist", status=status.HTTP_400_BAD_REQUEST
            )

        try:
            account_token = queryset[0]
            merge_api_service = MergeInvoiceApiService(account_token)

            line_items_payload = request.data.get("model")

            # prepare line items data
            line_items_data = []
            for line_item_payload in line_items_payload.get("line_items", []):
                line_item_data = {
                    "id": line_item_payload.get("id"),
                    "remote_id": line_item_payload.get("id"),
                    # "name": line_item_payload.get("item"),
                    # "status": line_item_payload.get("status"),
                    "unit_price": line_item_payload.get("unit_price"),
                    # "purchase_price": line_item_payload.get("purchase_price"),
                    # "TaxType": line_item_payload.get("TaxType"),
                    # "purchase_account": line_item_payload.get("purchase_account"),
                    "currency": line_item_payload.get("currency"),
                    "exchange_rate": line_items_payload.get("exchange_rate"),
                    "remote_updated_at": line_item_payload.get("remote_updated_at"),
                    "remote_was_deleted": line_item_payload.get("remote_was_deleted"),
                    "description": line_item_payload.get("item"),
                    "quantity": line_item_payload.get("quantity"),
                    "created_at": line_item_payload.get("created_at"),
                    "tracking_categories": line_items_payload.get(
                        "tracking_categories"
                    ),
                    "integration_params": {
                        "tax_rate_remote_id": line_item_payload.get(
                            "tax_rate_remote_id"
                        )
                    },
                    "account": line_item_payload.get("account"),
                    "remote_data": line_item_payload.get("remote_data"),
                }
                line_items_data.append(line_item_data)

            # prepare invoice data
            invoice_data = {
                "id": line_items_payload.get("id"),
                "remote_id": line_items_payload.get("remote_id"),
                "type": line_items_payload.get("type"),
                "due_date": line_items_payload.get("due_date"),
                "issue_date": line_items_payload.get("issue_date"),
                "contact": line_items_payload.get("contact"),
                "number": line_items_payload.get("number"),
                "memo": line_items_payload.get("memo"),
                "status": line_items_payload.get("status"),
                "company": line_items_payload.get("company"),
                "currency": line_items_payload.get("currency"),
                "tracking_categories": line_items_payload.get("tracking_categories"),
                "sub_total": line_items_payload.get("sub_total"),
                "total_tax_amount": line_items_payload.get("total_tax_amount"),
                "total_amount": line_items_payload.get("total_amount"),
                "integration_params": {
                    "tax_application_type": line_items_payload.get(
                        "tax_application_type"
                    )
                },
                "line_items": [
                    InvoiceLineItemRequest(**line_item) for line_item in line_items_data
                ],
            }

            invoice_created = merge_api_service.create_invoice(invoice_data)

            model_id = invoice_data["id"]
            invoice_id = invoice_created.model.id
            update_invoices_erp_id(model_id, invoice_id)

            if invoice_created is None:
                return Response(
                    {"status": "error", "message": "Failed to create invoice in Merge"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # create attachment
            attachment_payload = {
                "id": line_items_payload.get("id"),
                "file_name": line_items_payload.get("attachment").get("file_name"),
                "file_url": line_items_payload.get("attachment").get("file_url"),
                "integration_params": {
                    "transaction_id": invoice_id,
                    "transaction_name": line_items_payload.get("attachment").get(
                        "transaction_name"
                    ),
                },
            }

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
        api_log(msg=".....Processing Invoice UPDATE request bloc.....")
        data = request.data
        serializer = InvoiceUpdateSerializer(data=data)
        api_log(msg=f"[SERIALIZER bloc in views file for UPDATE] :: {serializer}")
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.erp_link_token_id = serializer.validated_data.get("erp_link_token_id")
        api_log(msg="1")

        queryset = self.get_queryset()
        if queryset is None or queryset == []:
            api_log(msg="link token details are None or empty")
            return Response(
                "Account token doesn't exist", status=status.HTTP_400_BAD_REQUEST
            )

        try:
            api_log(msg="2")
            account_token = queryset[0]
            print("THIS IS INVOICE UPDATE view ACCOUNT TOKEN:: ", account_token)
            api_log(msg="3")
            print("[account token data] ::", account_token)
            merge_api_service = MergeInvoiceApiService(account_token)

            payload_data = request.data
            line_items = []
            api_log(msg="4")
            for line_item_data in payload_data["model"]["line_items"]:
                api_log(msg="5")
                line_item = {
                    "id": line_item_data.get("id"),
                    "remote_id": line_item_data.get("remote_id"),
                    "unit_price": float(line_item_data.get("unit_price") if line_item_data.get("unit_price") is not None else 0),
                    "currency": line_item_data.get("currency"),
                    "exchange_rate": line_item_data.get("exchange_rate"),
                    "remote_was_deleted": line_item_data.get("remote_was_deleted"),
                    "description": line_item_data.get("description"),
                    "quantity": float(line_item_data.get("quantity") if line_item_data.get("quantity") is not None else 0),
                    "created_at": line_item_data.get("created_at"),
                    # "modified_at": line_item_data.get("modified_at"),
                    # "total_amount": float(line_item_data.get("total_amount") if line_item_data.get("total_amount") is not None else 0),
                    # "item": line_item_data.get("item"),
                    # "tracking_category": line_item_data.get("tracking_category"),
                    "tracking_categories": line_item_data.get("tracking_categories"),
                    "integration_params": {
                        "tax_rate_remote_id": line_item_data.get(
                            "tax_rate_remote_id"
                        )
                    },
                    "account": line_item_data.get("account"),
                    # "company": line_item_data.get("company"),
                    # "field_mappings": line_item_data.get("field_mappings"),
                    "remote_data": line_item_data.get("remote_data"),
                }
                line_items.append(line_item)

                # Construct the payload dynamically
            # total_tax_amount = payload_data["model"].get("total_tax_amount", 0)
            # total_tax_amount_float = float(total_tax_amount)
            # formatted_value = float("{:.2f}".format(total_tax_amount_float))
            payload = {
                "model": {
                    "id": invoice_id,
                    "remote_id": payload_data["model"].get("remote_id"),
                    "type": payload_data["model"].get("type"),
                    # "created_at": payload_data["model"].get("created_at"),
                    # "modified_at": payload_data["model"].get("modified_at"),
                    "due_date": payload_data["model"].get("due_date"),
                    "issue_date": payload_data["model"].get("issue_date"),
                    "contact": payload_data["model"].get("contact"),
                    "number": payload_data["model"].get("number"),
                    "memo": payload_data["model"].get("memo"),
                    "status": payload_data["model"].get("status"),
                    "company": payload_data["model"].get("company"),
                    "currency": payload_data["model"].get("currency"),
                    "tracking_categories": payload_data["model"].get("tracking_categories"),
                    "sub_total": float(payload_data["model"].get("sub_total") if payload_data["model"].get("sub_total") is not None else 0),
                    "total_tax_amount": float(payload_data["model"].get("total_tax_amount") if payload_data["model"].get("total_tax_amount") is not None else 0),
                    "total_amount": float(payload_data["model"].get("total_amount") if payload_data["model"].get("total_amount") is not None else 0),
                    "integration_params": {
                        "tax_application_type": payload_data["model"].get("tax_application_type")
                    },
                    # "exchange_rate": payload_data["model"].get("exchange_rate"),
                    # "total_discount": float(payload_data["model"].get("total_discount") if payload_data["model"].get("total_discount") is not None else 0),
                    # "balance": float(payload_data["model"].get("balance") if payload_data["model"].get("balance") is not None else 0),
                    # "remote_updated_at": payload_data["model"].get("remote_updated_at"),
                    # "payments": payload_data["model"].get("payments"),
                    # "applied_payments": payload_data["model"].get("applied_payments"),
                    "line_items": line_items,
                    # "line_items": [
                    #     InvoiceLineItemRequest(**line_item) for line_item in line_items
                    # ],
                },
                "warnings": [],
                "errors": [],
            }
            api_log(msg="6")

            api_log(msg=f"[PAYLOAD FOR INVOICE PATCH view file] : {payload}")
            update_response = merge_api_service.update_invoice(invoice_id, payload)
            api_log(msg=f"UPDATE INVOICE method response: {update_response}")

            if update_response is not None:
                api_log(msg="7")
                return Response(
                    {"status": "success", "message": "successfully update invoice in Merge"},
                    status=status.HTTP_200_OK,)
            else:
                api_log(msg="8")
                return Response(
                    {"status": "error", "message": "Couldn't update invoice in Merge"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR, )

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

        merge_invoice_api_service = MergeInvoiceApiService(self.link_token_details)
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

                invoices_json = format_merge_invoice_data(
                    invoice_response, erp_link_token_id, org_id
                )

                # save the data to the database
                api_log(msg="Invoices saving to database")

                kloo_service = KlooService(
                    auth_token=None,
                    erp_link_token_id=erp_link_token_id,
                )
                invoice_kloo_response = kloo_service.post_invoice_data(invoices_json)

                if invoice_kloo_response["status_code"] == status.HTTP_201_CREATED:
                    api_log(msg="data inserted successfully in the kloo Invoice system")
                    return Response(
                        {"message": "API Invoice Info completed successfully"}
                    )

                else:
                    return Response(
                        {"error": "Failed to send data to Kloo Contacts API"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        except Exception as e:
            error_message = f"Failed to send data to Kloo Invoice API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response("Failed to insert data to the kloo Invoice system")
