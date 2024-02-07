"""
Module docstring: This module provides functions related to traceback.
"""
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge.client import Merge
from merge.resources.accounting import PurchaseOrdersListRequestExpand, PurchaseOrdersRetrieveRequestExpand
from merge_integration import settings
from merge_integration.helper_functions import api_log


class MergePOList(APIView):
    """
    API endpoint for retrieving a list of purchase orders from the Merge system.
    """

    @staticmethod
    def get_pos():
        """
        Retrieves a list of purchase orders from the Merge system.

        Returns:
            The list of purchase orders.
        """
        api_log(msg="Processing GET request Merge purchase orders list")
        po_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN,
                          api_key=settings.API_KEY)
        try:
            po_data = po_client.accounting.purchase_orders.list(
                expand=PurchaseOrdersListRequestExpand.ACCOUNTING_PERIOD,
                remote_fields="status",
                show_enum_origins="status",
            )
            return po_data
        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                         - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")

    @staticmethod
    def response_payload(po_data):
        """
        Formats the retrieved purchase orders data into the desired format.

        Args:
            po_data: The data retrieved from the Merge system.

        Returns:
            The formatted data.
        """
        field_mappings = [{
            "organization_defined_targets": {},
            "linked_account_defined_targets": {}}]

        formatted_data = []
        for po in po_data.results:
            formatted_entry = {
                "status": po.status,
                "issue_date": po.issue_date.isoformat() + "Z",
                "purchase_order_number": po.purchase_order_number,
                "delivery_date": po.delivery_date,
                "delivery_address": po.delivery_address,
                "customer": po.customer,
                "vendor": po.vendor,
                "memo": po.memo,
                "company": po.company,
                "total_amount": po.total_amount,
                "currency": po.currency,
                "exchange_rate": po.exchange_rate,
                "line_items": [
                    {
                        "remote_id": line.remote_id,
                        "description": line.description,
                        "unit_price": line.unit_price,
                        "quantity": line.quantity,
                        "item": line.item,
                        "account": line.account,
                        "tracking_category": line.tracking_category,
                        "tracking_categories": line.tracking_categories,
                        "tax_amount": line.tax_amount,
                        "total_line_amount": line.total_line_amount,
                        "currency": line.currency,
                        "exchange_rate": line.exchange_rate,
                        "company": line.company,
                        "remote_was_deleted": line.remote_was_deleted,
                        "id": line.id,
                        "created_at": line.created_at.isoformat() + "Z",
                        "modified_at": line.modified_at.isoformat() + "Z",
                    }
                    for line in po.line_items
                ],
                "tracking_categories": po.tracking_categories,
                "remote_created_at": po.remote_created_at,
                "remote_updated_at": po.remote_updated_at.isoformat() + "Z",
                "remote_was_deleted": po.remote_was_deleted,
                "accounting_period": po.accounting_period,
                "id": po.id,
                "remote_id": po.remote_id,
                "created_at": po.created_at.isoformat() + "Z",
                "modified_at": po.modified_at.isoformat() + "Z",
                "field_mappings": field_mappings,
                "remote_data": po.remote_data,
            }
            formatted_data.append(formatted_entry)
            kloo_format_json = {"purchase_orders": formatted_data}

        return kloo_format_json

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve a list of purchase orders.

        Returns:
            A Response containing the formatted purchase orders data.
        """
        api_log(msg="Processing GET request in MergePurchaseOrders")

        po_data = self.get_pos()
        formatted_data = self.response_payload(po_data)

        api_log(msg=f"FORMATTED DATA: {formatted_data} \
         - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_data, status=status.HTTP_200_OK)


class MergePODetails(APIView):
    """
    API endpoint for retrieving details of a specific purchase order from the Merge system.
    """

    @staticmethod
    def get(_, id=None):
        """
        Retrieves details of a specific purchase order from the Merge system.

        Args:
            _: Unused parameter (conventionally represents the request object).
            id: The ID of the purchase order to retrieve.

        Returns:
            A Response containing the details of the specified purchase order.
        """
        api_log(msg="Processing GET request Merge purchase orders list")
        po_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN,
                          api_key=settings.API_KEY)

        try:
            po_id_data = po_client.accounting.purchase_orders.retrieve(
                id=id,
                expand=PurchaseOrdersRetrieveRequestExpand.ACCOUNTING_PERIOD,
                remote_fields="status",
                show_enum_origins="status", )

            field_mappings = [{
                "organization_defined_targets": {},
                "linked_account_defined_targets": {},
            }]

            po_id_total_data = []
            total_id_data = {
                "status": po_id_data.status,
                "issue_date": po_id_data.issue_date,
                "purchase_order_number": po_id_data.purchase_order_number,
                "delivery_date": po_id_data.delivery_date,
                "delivery_address": po_id_data.delivery_address,
                "customer": po_id_data.customer,
                "vendor": po_id_data.vendor,
                "memo": po_id_data.memo,
                "company": po_id_data.company,
                "total_amount": po_id_data.total_amount,
                "currency": po_id_data.currency,
                "exchange_rate": po_id_data.exchange_rate,
                "line_items": [
                    {
                        "remote_id": line.remote_id,
                        "description": line.description,
                        "unit_price": line.unit_price,
                        "quantity": line.quantity,
                        "item": line.item,
                        "account": line.account,
                        "tracking_category": line.tracking_category,
                        "tracking_categories": line.tracking_categories,  # [],
                        "tax_amount": line.tax_amount,
                        "total_line_amount": line.total_line_amount,
                        "currency": line.currency,
                        "exchange_rate": line.exchange_rate,
                        "company": line.company,
                        "remote_was_deleted": line.remote_was_deleted,
                        "id": line.id,
                        "created_at": line.created_at,
                        "modified_at": line.modified_at,
                    }
                    for line in po_id_data.line_items
                ],
                "tracking_categories": po_id_data.tracking_categories,
                "remote_created_at": po_id_data.remote_created_at,
                "remote_updated_at": po_id_data.remote_updated_at,
                "remote_was_deleted": po_id_data.remote_was_deleted,
                "accounting_period": po_id_data.accounting_period,
                "id": po_id_data.id,
                "remote_id": po_id_data.remote_id,
                "created_at": po_id_data.created_at,
                "modified_at": po_id_data.modified_at,
                "field_mappings": field_mappings,
                "remote_data": po_id_data.remote_data,
            }
            po_id_total_data.append(total_id_data)

            api_log(
                msg=f"FORMATTED DATA: {po_id_total_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
            return Response(po_id_total_data, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
